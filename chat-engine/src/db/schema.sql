-- SQLite Schema for TrackOn Chat
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA foreign_keys = ON;

-- 1. Cryptographic Room Storage
CREATE TABLE IF NOT EXISTS rooms (
    room_id BLOB(6) PRIMARY KEY,              -- Public wire routing ID (6 bytes)
    room_alias TEXT NOT NULL,                 -- User-facing display name
    encrypted_key BLOB(48) NOT NULL,          -- Encrypted Master PRK
    key_iv BLOB(12) NOT NULL,                 -- Initialization vector for encrypted_key
    last_seq_out INTEGER NOT NULL DEFAULT 0,  -- Outgoing sequence counter
    last_seq_in INTEGER NOT NULL DEFAULT 0,   -- Ingoing sliding-window horizon (V_max)
    window_bitmask INTEGER NOT NULL DEFAULT 0,-- 64-bit sliding window register
    created_at INTEGER NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_rooms_id ON rooms(room_id);

-- 2. Token Dictionary Table
CREATE TABLE IF NOT EXISTS token_dictionary (
    token_id INTEGER PRIMARY KEY,             -- 16-bit unsigned integer (0x0000 - 0xFFFF)
    symbol TEXT NOT NULL UNIQUE,              -- Character, token, or common phrase
    weight INTEGER NOT NULL DEFAULT 1         -- Compression frequency priority
);

CREATE INDEX IF NOT EXISTS idx_token_symbol ON token_dictionary(symbol);

-- 3. Message Ledger (Decrypted Local Chat Store)
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,                      -- UUIDv7 or timestamp-id
    room_id BLOB(6) NOT NULL,
    direction INTEGER NOT NULL,               -- 0 = Incoming, 1 = Outgoing
    seq_num INTEGER NOT NULL,
    raw_tokens BLOB NOT NULL,                 -- Binary representation of token sequence
    resolved_text TEXT NOT NULL,              -- Full UTF-8 resolved string
    received_at INTEGER NOT NULL,             -- Local monotonic epoch
    FOREIGN KEY(room_id) REFERENCES rooms(room_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_messages_room_time ON messages(room_id, received_at DESC);

-- 4. Transient Relay Ring-Buffer (Prevents Broadcast Storms)
CREATE TABLE IF NOT EXISTS relay_cache (
    packet_hash BLOB(8) PRIMARY KEY,          -- 8-byte hash of (Room_ID || Nonce || Ciphertext)
    seen_at INTEGER NOT NULL,                 -- Millisecond timestamp
    hop_limit_remaining INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_relay_seen ON relay_cache(seen_at);

