import hashlib
import random
import time
from typing import Optional
from ..core.frame import TrackOnFrame
from ..db.storage import Database
from ..radio.broadcaster import BleBroadcaster

class MeshRouter:
    """
    Implements stochastic blind relay forwarding:
    - SipHash/Blake3-derived deduplication check in memory-mapped SQLite cache.
    - Hop count decrement (bits 7..5).
    - Randomized jitter delay (20ms - 150ms) to prevent broadcast storms.
    """

    def __init__(self, db: Database, broadcaster: BleBroadcaster):
        self.db = db
        self.broadcaster = broadcaster

    @staticmethod
    def compute_packet_hash(frame: TrackOnFrame) -> bytes:
        # Hash of Room_ID || Nonce || Ciphertext
        h = hashlib.sha256()
        h.update(frame.room_id)
        h.update(frame.nonce_counter.to_bytes(4, "big"))
        h.update(frame.ciphertext)
        return h.digest()[:8]

    def handle_relay(self, frame: TrackOnFrame) -> bool:
        """
        Processes blind relay routing. Returns True if frame was retransmitted.
        """
        pkt_hash = self.compute_packet_hash(frame)
        if self.db.is_relay_cached(pkt_hash):
            return False  # Already seen, silent drop

        decremented_frame = frame.decrement_hop()
        if decremented_frame is None:
            # Hop limit reached 0, drop
            self.db.add_relay_cache(pkt_hash, 0)
            return False

        # Jitter delay: 20ms to 150ms
        jitter_ms = random.randint(20, 150)
        time.sleep(jitter_ms / 1000.0)

        # Check again if another peer broadcasted in the meantime
        if self.db.is_relay_cached(pkt_hash):
            return False

        # Record in dedup cache
        self.db.add_relay_cache(pkt_hash, decremented_frame.hop_limit)

        # Blast 3 bursts with 20ms spacing
        raw_wire = decremented_frame.pack()
        self.broadcaster.broadcast_frame(raw_wire, bursts=3, burst_interval_ms=20)
        return True

