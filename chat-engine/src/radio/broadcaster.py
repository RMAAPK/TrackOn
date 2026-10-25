import subprocess
import time

class BleBroadcaster:
    """Emits raw ADV_NONCONN_IND bursts via BlueZ HCI socket commands."""

    def __init__(self, hci_name: str = "hci0"):
        self.hci_name = hci_name

    def broadcast_frame(self, frame_bytes: bytes, bursts: int = 3, burst_interval_ms: int = 20):
        """
        Loads the 31-byte frame into the radio advertising buffer and emits bursts.
        """
        assert len(frame_bytes) == 31, f"Expected 31 bytes, got {len(frame_bytes)}"

        # hcitool cmd 0x08 0x0008 expects: <len> <payload_bytes...>
        # Here len is 0x1F (31 decimal)
        hex_args = [f"{len(frame_bytes):02x}"] + [f"{b:02x}" for b in frame_bytes]
        cmd = ["hcitool", "-i", self.hci_name, "cmd", "0x08", "0x0008"] + hex_args

        # 1. Set Advertising Data
        subprocess.run(cmd, capture_output=True)

        # 2. Enable Non-connectable Undirected Advertising (ADV_NONCONN_IND)
        subprocess.run(["hciconfig", self.hci_name, "leadv", "3"], capture_output=True)

        # 3. Burst timing
        for _ in range(bursts):
            time.sleep(burst_interval_ms / 1000.0)

    def stop(self):
        subprocess.run(["hciconfig", self.hci_name, "noleadv"], capture_output=True)

