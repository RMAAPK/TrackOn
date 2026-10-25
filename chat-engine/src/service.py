import os
import sys
from ..core.crypto import TrackOnCrypto
from ..core.frame import TrackOnFrame
from ..core.tokens import TokenCodec
from ..core.window import SlidingWindow
from ..db.storage import Database
from ..radio.broadcaster import BleBroadcaster
from ..radio.sniffer import BleSniffer
from ..radio.rfkill_manager import RadioManager
from ..mesh.router import MeshRouter

class TrackOnDaemon:
    """Central coordinator for TrackOn Chat airgapped mesh daemon."""

    def __init__(self, db_path: str = "trackon_chat.db", hci_name: str = "hci0"):
        self.db = Database(db_path)
        self.hci_name = hci_name
        self.broadcaster = BleBroadcaster(hci_name)
        self.router = MeshRouter(self.db, self.broadcaster)
        self.codec = TokenCodec()
        self.crypto_instances = {}  # room_id -> TrackOnCrypto
        self.windows = {}           # room_id -> SlidingWindow
        self.sniffer = None
        self._load_active_rooms()

    def _load_active_rooms(self):
        rooms = self.db.list_rooms()
        for r in rooms:
            room_id = bytes(r["room_id"])
            master_secret = bytes(r["encrypted_key"])
            crypto = TrackOnCrypto(master_secret)
            self.crypto_instances[room_id] = crypto
            self.windows[room_id] = SlidingWindow(r["last_seq_in"], r["window_bitmask"])

    def create_or_join_room(self, alias: str, master_secret: bytes) -> bytes:
        crypto = TrackOnCrypto(master_secret)
        room_id = crypto.room_id
        self.db.add_room(room_id, alias, master_secret)
        self.crypto_instances[room_id] = crypto
        self.windows[room_id] = SlidingWindow(0, 0)
        return room_id

    def send_message(self, room_id: bytes, text: str, hop_limit: int = 4) -> bool:
        if room_id not in self.crypto_instances:
            raise ValueError("Room not registered on this node")

        crypto = self.crypto_instances[room_id]
        seq = self.db.next_outgoing_seq(room_id)

        # 1. Tokenize plaintext
        raw_tokens = self.codec.encode(text)

        # 2. Encapsulate with ChaCha20 & MAC
        # Mode = 0 (single frame)
        nonce_high = (seq >> 24) & 0x0F
        routing_byte = ((hop_limit & 0x07) << 5) | nonce_high
        ciphertext, mac_tag = crypto.encrypt_payload(raw_tokens, routing_byte, seq)

        # 3. Assemble 31-byte frame
        frame = TrackOnFrame(
            room_id=room_id,
            hop_limit=hop_limit,
            is_multipart=False,
            nonce_counter=seq,
            ciphertext=ciphertext,
            mac_tag=mac_tag,
        )

        wire_bytes = frame.pack()

        # 4. Save to local SQLite
        self.db.add_message(room_id, direction=1, seq_num=seq, raw_tokens=raw_tokens, resolved_text=text)

        # 5. Broadcast frame
        self.broadcaster.broadcast_frame(wire_bytes, bursts=3, burst_interval_ms=20)
        return True

    def on_frame_received(self, raw_wire: bytes):
        frame = TrackOnFrame.unpack(raw_wire)
        if not frame:
            return

        # Check if we own this room key
        if frame.room_id in self.crypto_instances:
            crypto = self.crypto_instances[frame.room_id]
            window = self.windows[frame.room_id]

            # Anti-replay sliding window validation
            if not window.validate_and_update(frame.nonce_counter):
                return  # Replay rejected

            # Canonical AAD check and decryption
            aad = frame.canonical_aad()
            mode_bit = 1 if frame.is_multipart else 0
            routing_byte = (mode_bit << 4) | ((frame.nonce_counter >> 24) & 0x0F)
            plaintext = crypto.decrypt_payload(
                frame.ciphertext,
                frame.mac_tag,
                aad,
                routing_byte,
                frame.nonce_counter
            )

            if plaintext is not None:
                decoded_text = self.codec.decode(plaintext)
                self.db.add_message(
                    frame.room_id,
                    direction=0,
                    seq_num=frame.nonce_counter,
                    raw_tokens=plaintext,
                    resolved_text=decoded_text
                )
                self.db.update_incoming_window(frame.room_id, window.v_max, window.bitmask)
                print(f"[RECV] Room: {frame.room_id.hex()} | Seq: {frame.nonce_counter} | Text: '{decoded_text}'")
                return

        # If not owned or decryption failed, treat as blind relay
        self.router.handle_relay(frame)

    def start(self):
        RadioManager.initialize_adapter(self.hci_name)
        self.sniffer = BleSniffer(self.hci_name, callback=self.on_frame_received)
        self.sniffer.start()
        print(f"[+] TrackOn Mesh Daemon online on {self.hci_name}.")

    def stop(self):
        if self.sniffer:
            self.sniffer.stop()
        self.broadcaster.stop()
        RadioManager.teardown_adapter(self.hci_name)
        print("[+] TrackOn Mesh Daemon stopped.")

