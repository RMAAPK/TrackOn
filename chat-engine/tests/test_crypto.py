import os
import sys
import unittest
from pathlib import Path

# Add src to python path
src_dir = str(Path(__file__).resolve().parent.parent / "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from core.crypto import TrackOnCrypto
from core.frame import TrackOnFrame
from core.tokens import TokenCodec
from core.window import SlidingWindow

class TestTrackOnChatProtocol(unittest.TestCase):

    def setUp(self):
        self.master_seed = b"\x42" * 32
        self.crypto = TrackOnCrypto(self.master_seed)
        self.codec = TokenCodec()

    def test_key_derivation(self):
        # Verify 6-byte room ID derivation
        self.assertEqual(len(self.crypto.room_id), 6)
        self.assertEqual(len(self.crypto.k_enc), 32)
        self.assertEqual(len(self.crypto.ratchet_root), 32)

    def test_token_codec(self):
        text = "wa"
        encoded = self.codec.encode(text)
        self.assertEqual(len(encoded), 10)
        decoded = self.codec.decode(encoded)
        self.assertEqual(decoded, "wa")

    def test_frame_pack_unpack(self):
        room_id = self.crypto.room_id
        hop_limit = 4
        is_multipart = False
        seq = 105
        raw_tokens = self.codec.encode("wa")
        ciphertext, mac_tag = self.crypto.encrypt_payload(raw_tokens, 0, seq)

        frame = TrackOnFrame(
            room_id=room_id,
            hop_limit=hop_limit,
            is_multipart=is_multipart,
            nonce_counter=seq,
            ciphertext=ciphertext,
            mac_tag=mac_tag
        )

        wire = frame.pack()
        self.assertEqual(len(wire), 31)

        unpacked = TrackOnFrame.unpack(wire)
        self.assertIsNotNone(unpacked)
        self.assertEqual(unpacked.room_id, room_id)
        self.assertEqual(unpacked.hop_limit, hop_limit)
        self.assertEqual(unpacked.nonce_counter, seq)
        self.assertEqual(unpacked.ciphertext, ciphertext)
        self.assertEqual(unpacked.mac_tag, mac_tag)

    def test_encryption_and_tamper_resistance(self):
        seq = 1
        raw_tokens = self.codec.encode("SOS")
        ciphertext, mac_tag = self.crypto.encrypt_payload(raw_tokens, 0, seq)

        frame = TrackOnFrame(
            room_id=self.crypto.room_id,
            hop_limit=3,
            is_multipart=False,
            nonce_counter=seq,
            ciphertext=ciphertext,
            mac_tag=mac_tag
        )

        # Valid decryption
        aad = frame.canonical_aad()
        plaintext = self.crypto.decrypt_payload(frame.ciphertext, frame.mac_tag, aad, 0, seq)
        self.assertIsNotNone(plaintext)
        self.assertEqual(self.codec.decode(plaintext), "SOS")

        # Tampered ciphertext fails
        tampered_cipher = bytearray(frame.ciphertext)
        tampered_cipher[0] ^= 0xFF
        fail_res = self.crypto.decrypt_payload(bytes(tampered_cipher), frame.mac_tag, aad, 0, seq)
        self.assertIsNone(fail_res)

    def test_sliding_window_anti_replay(self):
        window = SlidingWindow()
        # Accept packet 1
        self.assertTrue(window.validate_and_update(1))
        # Replay packet 1 fails
        self.assertFalse(window.validate_and_update(1))
        # Out-of-order within 64: send 10, then 5
        self.assertTrue(window.validate_and_update(10))
        self.assertTrue(window.validate_and_update(5))
        # Replay 5 fails
        self.assertFalse(window.validate_and_update(5))
        # Beyond 64 fails
        self.assertTrue(window.validate_and_update(100))
        self.assertFalse(window.validate_and_update(10)) # 100 - 10 = 90 >= 64

if __name__ == "__main__":
    unittest.main()

