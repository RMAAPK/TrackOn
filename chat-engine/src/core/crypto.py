import struct
from cryptography.hazmat.primitives.kdf.hkdf import HKDF, HKDFExpand
from cryptography.hazmat.primitives import hashes, hmac
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms

SALT_TRACKON = b"TrackOn"
INFO_ROOM_WIRE = b"trackon-wire-room"
INFO_AEAD_KEY = b"trackon-aead-key"
INFO_RATCHET = b"trackon-ratchet"

class TrackOnCrypto:
    """
    Implements the HKDF key derivation tree, ChaCha20 encryption/decryption,
    and Poly1305/HMAC 32-bit truncated authentication.
    """

    def __init__(self, master_secret: bytes):
        if len(master_secret) != 32:
            raise ValueError(f"Master secret must be 32 bytes, got {len(master_secret)}")
        self.master_secret = master_secret
        
        # Step 1: HKDF-Extract(Salt="TrackOn", IKM=MasterSecret) -> PRK (32B)
        hkdf_extract = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=SALT_TRACKON,
            info=b"",
        )
        self.prk = hkdf_extract.derive(self.master_secret)

        # Step 2: HKDF-Expand -> Room Wire ID (6B)
        self.room_id = HKDFExpand(
            algorithm=hashes.SHA256(),
            length=6,
            info=INFO_ROOM_WIRE,
        ).derive(self.prk)

        # Step 3: HKDF-Expand -> K_enc (32B)
        self.k_enc = HKDFExpand(
            algorithm=hashes.SHA256(),
            length=32,
            info=INFO_AEAD_KEY,
        ).derive(self.prk)

        # Step 4: HKDF-Expand -> Ratchet Root (32B)
        self.ratchet_root = HKDFExpand(
            algorithm=hashes.SHA256(),
            length=32,
            info=INFO_RATCHET,
        ).derive(self.prk)

    @staticmethod
    def build_nonce(routing_byte: int, counter: int) -> bytes:
        """
        Builds 16-byte nonce for ChaCha20:
        Prefix: 8 bytes of zeroes
        Routing Byte: 1 byte (canonical with hop=0)
        Counter: 3 bytes
        Pad: 4 bytes of zeroes to reach 16 bytes
        """
        nonce_high = counter >> 24
        mode_bit = (routing_byte >> 4) & 0x01
        norm_routing = ((0 & 0x07) << 5) | (mode_bit << 4) | (nonce_high & 0x0F)
        seq_low = struct.pack(">I", counter & 0x00FFFFFF)[1:]
        return b"\x00" * 8 + bytes([norm_routing]) + seq_low + b"\x00" * 4

    def compute_mac(self, aad: bytes, ciphertext: bytes) -> bytes:
        """Computes truncated 32-bit (4-byte) authentication tag."""
        h = hmac.HMAC(self.k_enc, hashes.SHA256())
        h.update(aad)
        h.update(ciphertext)
        digest = h.finalize()
        return digest[:4]

    def encrypt_payload(self, plaintext: bytes, routing_byte: int, counter: int) -> tuple[bytes, bytes]:
        """
        Encrypts up to 10 bytes using ChaCha20 and returns (ciphertext, mac_tag).
        """
        if len(plaintext) > 10:
            raise ValueError(f"Payload maximum 10 bytes, got {len(plaintext)}")
        
        # Pad plaintext to exactly 10 bytes
        padded = plaintext.ljust(10, b"\x00")
        nonce = self.build_nonce(routing_byte, counter)

        cipher = Cipher(algorithms.ChaCha20(self.k_enc, nonce), mode=None)
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded)

        # AAD: Room_ID (6B) || Canonical Routing Byte || Counter (3B)
        nonce_high = counter >> 24
        mode_bit = (routing_byte >> 4) & 0x01
        norm_routing = ((0 & 0x07) << 5) | (mode_bit << 4) | (nonce_high & 0x0F)
        seq_low = struct.pack(">I", counter & 0x00FFFFFF)[1:]
        aad = self.room_id + bytes([norm_routing]) + seq_low

        mac_tag = self.compute_mac(aad, ciphertext)
        return ciphertext, mac_tag

    def decrypt_payload(self, ciphertext: bytes, mac_tag: bytes, aad: bytes, routing_byte: int, counter: int) -> bytes | None:
        """Verifies 32-bit MAC tag and decrypts ciphertext using ChaCha20."""
        expected_tag = self.compute_mac(aad, ciphertext)
        if expected_tag != mac_tag:
            return None  # Authentication failed

        nonce = self.build_nonce(routing_byte, counter)
        cipher = Cipher(algorithms.ChaCha20(self.k_enc, nonce), mode=None)
        decryptor = cipher.decryptor()
        plaintext = decryptor.update(ciphertext)
        return plaintext

