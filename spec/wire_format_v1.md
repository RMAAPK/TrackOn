# TRACKON CHAT WIRE FORMAT SPECIFICATION (v1.0-RC1)

Every legacy BLE advertisement payload has a strict maximum of 31 octets.
The TrackOn Chat frame consumes exactly 31 octets:

```text
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Len: 0x02    |  Type: 0x01   |  Flags: 0x06  |  Len: 0x1B    |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Type: 0xFF   | Company ID: 0x4C5D (LE: 0x5D, 0x4C)           |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                   Room ID (Bytes 0..3)                        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|   Room ID (Bytes 4..5)        | Hop:3 | Mode:1| Epoch Nonce   |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                     Epoch Nonce (cont.)                       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                 Encrypted Payload (10 Bytes)                  |
|                 (Tokenized Dictionary Coordinates)            |
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|             Truncated Authentication Tag (32-bit MAC)         |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

## Field Breakdown:
1. **Octet 00–02 (`02 01 06`):** GAP Flags: 2 bytes, Type `0x01` (Flags), Value `0x06` (`LE General Discoverable` + `BR/EDR Not Supported`).
2. **Octet 03–04 (`1B FF`):** Manufacturer Element: 27 bytes follow, Type `0xFF` (Manufacturer Specific Data).
3. **Octet 05–06 (`5D 4C`):** Assigned Shard Company ID `0x4C5D` in Little-Endian. Baseband chips discard mismatched packets here with 0% CPU wake.
4. **Octet 07–12 (`6 Bytes`):** Room Wire ID. Derived deterministically via HKDF from the shared room master key.
5. **Octet 13 (`1 Byte`):** Routing & Control Byte:
   - Bits `7..5` (3 bits): Hop-Limit / TTL ($0 \text{ to } 7$). Decremented by each blind relay.
   - Bit `4` (1 bit): Packet Type (`0` = Single Frame, `1` = Multi-Part Fragment).
   - Bits `3..0` (4 bits): Nonce High Nibble.
6. **Octet 14–16 (`3 Bytes`):** Monotonic Sequence Counter / Epoch Nonce (28-bit total combined counter).
7. **Octet 17–26 (`10 Bytes`):** Encrypted Payload (Ciphertext). Carries up to 5 token pairs ($5 \times \text{uint16}$) or compressed symbols.
8. **Octet 27–30 (`4 Bytes`):** Truncated Poly1305 / HMAC Tag (32-bit integrity check).

