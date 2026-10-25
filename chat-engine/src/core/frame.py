import struct
from typing import Tuple, Optional

COMPANY_ID = 0x4C5D  # Little endian: 0x5D, 0x4C

class TrackOnFrame:
    """
    Encapsulates and decapsulates the strict 31-byte legacy BLE advertisement frame.
    
    Wire Layout (31 bytes):
    - [0..2]   GAP Flags (3B): 02 01 06
    - [3..4]   Manufacturer Header (2B): 1B FF (Len 27, Type 0xFF)
    - [5..6]   Company ID (2B): 5D 4C (0x4C5D)
    - [7..12]  Room Wire ID (6B): derived via HKDF
    - [13]     Routing Byte (1B): [7..5: Hop-Limit (0..7)] [4: Mode] [3..0: Nonce High]
    - [14..16] Epoch / Sequence Counter (3B): Monotonic counter low 24 bits
    - [17..26] Ciphertext (10B): Encrypted payload
    - [27..30] MAC Tag (4B): Truncated 32-bit Poly1305 / HMAC tag
    """

    def __init__(
        self,
        room_id: bytes,
        hop_limit: int,
        is_multipart: bool,
        nonce_counter: int,
        ciphertext: bytes,
        mac_tag: bytes,
    ):
        if len(room_id) != 6:
            raise ValueError(f"Room ID must be 6 bytes, got {len(room_id)}")
        if len(ciphertext) != 10:
            raise ValueError(f"Ciphertext must be exactly 10 bytes, got {len(ciphertext)}")
        if len(mac_tag) != 4:
            raise ValueError(f"MAC tag must be 4 bytes, got {len(mac_tag)}")
        if not (0 <= hop_limit <= 7):
            raise ValueError(f"Hop limit must be 0..7, got {hop_limit}")

        self.room_id = room_id
        self.hop_limit = hop_limit
        self.is_multipart = is_multipart
        self.nonce_counter = nonce_counter & 0x0FFFFFFF  # 28-bit
        self.ciphertext = ciphertext
        self.mac_tag = mac_tag

    def pack(self) -> bytes:
        flags = bytes([0x02, 0x01, 0x06])
        mfg_header = bytes([0x1B, 0xFF])
        comp_id = struct.pack("<H", COMPANY_ID)  # 5D 4C

        # Routing byte:
        # Bits 7..5: hop_limit (3 bits)
        # Bit 4: mode (1 bit)
        # Bits 3..0: nonce counter highest 4 bits (bits 27..24)
        nonce_high_nibble = (self.nonce_counter >> 24) & 0x0F
        mode_bit = 1 if self.is_multipart else 0
        routing_byte = ((self.hop_limit & 0x07) << 5) | ((mode_bit & 0x01) << 4) | nonce_high_nibble

        # Nonce counter lowest 24 bits
        seq_low = struct.pack(">I", self.nonce_counter & 0x00FFFFFF)[1:]  # 3 bytes big-endian

        frame = (
            flags
            + mfg_header
            + comp_id
            + self.room_id
            + bytes([routing_byte])
            + seq_low
            + self.ciphertext
            + self.mac_tag
        )
        assert len(frame) == 31, f"Frame length must be 31, got {len(frame)}"
        return frame

    @classmethod
    def unpack(cls, raw: bytes) -> Optional["TrackOnFrame"]:
        if len(raw) != 31:
            return None

        # Check flags and manufacturer header
        if raw[0:3] != b"\x02\x01\x06" or raw[3:5] != b"\x1b\xff":
            return None

        # Check Company ID
        comp_id = struct.unpack("<H", raw[5:7])[0]
        if comp_id != COMPANY_ID:
            return None

        room_id = raw[7:13]
        routing_byte = raw[13]
        hop_limit = (routing_byte >> 5) & 0x07
        is_multipart = bool((routing_byte >> 4) & 0x01)
        nonce_high = routing_byte & 0x0F

        seq_low = struct.unpack(">I", b"\x00" + raw[14:17])[0]
        nonce_counter = (nonce_high << 24) | seq_low

        ciphertext = raw[17:27]
        mac_tag = raw[27:31]

        return cls(
            room_id=room_id,
            hop_limit=hop_limit,
            is_multipart=is_multipart,
            nonce_counter=nonce_counter,
            ciphertext=ciphertext,
            mac_tag=mac_tag,
        )

    def canonical_aad(self) -> bytes:
        """
        Builds the canonical Associated Authenticated Data (AAD) for MAC evaluation.
        Hop-limit is normalized to 0 so relays decrementing TTL do not invalidate the sender tag.
        """
        nonce_high_nibble = (self.nonce_counter >> 24) & 0x0F
        mode_bit = 1 if self.is_multipart else 0
        norm_routing = ((0 & 0x07) << 5) | ((mode_bit & 0x01) << 4) | nonce_high_nibble
        seq_low = struct.pack(">I", self.nonce_counter & 0x00FFFFFF)[1:]
        return self.room_id + bytes([norm_routing]) + seq_low

    def decrement_hop(self) -> Optional["TrackOnFrame"]:
        if self.hop_limit <= 1:
            return None
        return TrackOnFrame(
            room_id=self.room_id,
            hop_limit=self.hop_limit - 1,
            is_multipart=self.is_multipart,
            nonce_counter=self.nonce_counter,
            ciphertext=self.ciphertext,
            mac_tag=self.mac_tag,
        )

