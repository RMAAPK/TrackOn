import struct
import json
from pathlib import Path
from typing import List, Optional

class TokenCodec:
    """
    Compresses plain text into 2-byte token coordinates and expands them back.
    Up to 5 token coordinates (10 bytes total) per frame.
    """

    def __init__(self, dict_path: Optional[str] = None):
        self.sym_to_id = {}
        self.id_to_sym = {}

        if dict_path is None:
            # Look for default dictionary
            base = Path(__file__).resolve().parent.parent.parent
            dict_path = str(base / "spec" / "dictionary_v1.json")

        if Path(dict_path).exists():
            with open(dict_path, "r", encoding="utf-8") as f:
                entries = json.load(f)
                for item in entries:
                    tid = item["id"]
                    sym = item["symbol"]
                    self.sym_to_id[sym] = tid
                    self.id_to_sym[tid] = sym
        else:
            # Fallback basic mapping
            for idx in range(256):
                ch = chr(idx)
                self.sym_to_id[ch] = idx
                self.id_to_sym[idx] = ch

    def encode(self, text: str) -> bytes:
        """
        Encodes up to 5 symbols into 10 bytes (5 x uint16 big-endian).
        """
        tokens: List[int] = []
        i = 0
        while i < len(text) and len(tokens) < 5:
            # Check 4-character phrase match first
            matched = False
            for span in (4, 3, 2):
                if i + span <= len(text):
                    sub = text[i:i+span]
                    if sub in self.sym_to_id:
                        tokens.append(self.sym_to_id[sub])
                        i += span
                        matched = True
                        break
            if not matched:
                ch = text[i]
                if ch in self.sym_to_id:
                    tokens.append(self.sym_to_id[ch])
                elif ch.lower() in self.sym_to_id:
                    tokens.append(self.sym_to_id[ch.lower()])
                else:
                    tokens.append(0)  # PAD
                i += 1

        # Pad with 0 up to 5 tokens
        while len(tokens) < 5:
            tokens.append(0)

        # Pack into 10 bytes
        return struct.pack(">5H", *tokens[:5])

    def decode(self, raw_bytes: bytes) -> str:
        """
        Decodes 10 bytes (5 x uint16) into string.
        """
        if len(raw_bytes) != 10:
            raise ValueError(f"Expected 10 bytes, got {len(raw_bytes)}")
        tokens = struct.unpack(">5H", raw_bytes)
        result = []
        for tid in tokens:
            if tid == 0:
                continue
            sym = self.id_to_sym.get(tid, "")
            result.append(sym)
        return "".join(result)

