import sqlite3
import time
import uuid
from pathlib import Path
from typing import Optional, List, Tuple

class Database:
    def __init__(self, db_path: str = "trackon_chat.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        schema_path = Path(__file__).resolve().parent / "schema.sql"
        if schema_path.exists():
            with open(schema_path, "r", encoding="utf-8") as f:
                self.conn.executescript(f.read())
        self.conn.commit()

    def add_room(self, room_id: bytes, room_alias: str, master_secret: bytes):
        now = int(time.time())
        # In this reference daemon, encrypted_key holds master_secret with empty IV
        self.conn.execute(
            """
            INSERT OR REPLACE INTO rooms (room_id, room_alias, encrypted_key, key_iv, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (room_id, room_alias, master_secret, b"\x00" * 12, now)
        )
        self.conn.commit()

    def get_room(self, room_id: bytes) -> Optional[sqlite3.Row]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM rooms WHERE room_id = ?", (room_id,))
        return cur.fetchone()

    def list_rooms(self) -> List[sqlite3.Row]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM rooms ORDER BY created_at DESC")
        return cur.fetchall()

    def next_outgoing_seq(self, room_id: bytes) -> int:
        cur = self.conn.cursor()
        cur.execute("SELECT last_seq_out FROM rooms WHERE room_id = ?", (room_id,))
        row = cur.fetchone()
        current = row["last_seq_out"] if row else 0
        nxt = current + 1
        self.conn.execute(
            "UPDATE rooms SET last_seq_out = ? WHERE room_id = ?",
            (nxt, room_id)
        )
        self.conn.commit()
        return nxt

    def update_incoming_window(self, room_id: bytes, v_max: int, bitmask: int):
        self.conn.execute(
            "UPDATE rooms SET last_seq_in = ?, window_bitmask = ? WHERE room_id = ?",
            (v_max, bitmask, room_id)
        )
        self.conn.commit()

    def add_message(self, room_id: bytes, direction: int, seq_num: int, raw_tokens: bytes, resolved_text: str):
        msg_id = str(uuid.uuid4())
        now = int(time.time())
        self.conn.execute(
            """
            INSERT INTO messages (id, room_id, direction, seq_num, raw_tokens, resolved_text, received_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (msg_id, room_id, direction, seq_num, raw_tokens, resolved_text, now)
        )
        self.conn.commit()

    def get_messages(self, room_id: bytes, limit: int = 50) -> List[sqlite3.Row]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM messages WHERE room_id = ? ORDER BY received_at DESC LIMIT ?",
            (room_id, limit)
        )
        return cur.fetchall()

    def is_relay_cached(self, packet_hash: bytes) -> bool:
        cur = self.conn.cursor()
        cur.execute("SELECT seen_at FROM relay_cache WHERE packet_hash = ?", (packet_hash,))
        return cur.fetchone() is not None

    def add_relay_cache(self, packet_hash: bytes, hop_remaining: int):
        now = int(time.time())
        self.conn.execute(
            "INSERT OR REPLACE INTO relay_cache (packet_hash, seen_at, hop_limit_remaining) VALUES (?, ?, ?)",
            (packet_hash, now, hop_remaining)
        )
        # Purge entries older than 60 seconds
        self.conn.execute("DELETE FROM relay_cache WHERE seen_at < ?", (now - 60,))
        self.conn.commit()

