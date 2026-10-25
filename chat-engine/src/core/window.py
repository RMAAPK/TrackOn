class SlidingWindow:
    """
    64-bit sliding window anti-replay protector.
    Tracks highest sequence counter (v_max) and a 64-bit bitmask register.
    """

    def __init__(self, v_max: int = 0, bitmask: int = 0):
        self.v_max = v_max
        self.bitmask = bitmask

    def validate_and_update(self, seq_num: int) -> bool:
        """
        Validates whether seq_num is valid and unseen.
        Returns True if accepted (and updates window), False if replayed/expired.
        """
        if seq_num > self.v_max:
            # Shift window right by delta
            delta = seq_num - self.v_max
            if delta >= 64:
                self.bitmask = 1  # Brand new window, only bit 0 set
            else:
                self.bitmask = (self.bitmask << delta) | 1
                self.bitmask &= (1 << 64) - 1  # Keep 64 bits
            self.v_max = seq_num
            return True
        else:
            delta = self.v_max - seq_num
            if delta >= 64:
                # Outside sliding window: expired
                return False
            # Check bit at offset delta
            if (self.bitmask >> delta) & 1:
                # Already received
                return False
            # Mark bit as received
            self.bitmask |= (1 << delta)
            return True

