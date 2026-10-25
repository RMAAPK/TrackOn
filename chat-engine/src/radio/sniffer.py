import subprocess
import threading
from typing import Callable, Optional

class BleSniffer(threading.Thread):
    """
    Sniffs raw HCI frames from the controller using btmon.
    Filters frames containing Company ID 0x4C5D and delivers them to the callback.
    """

    def __init__(self, hci_name: str = "hci0", callback: Optional[Callable[[bytes], None]] = None):
        super().__init__()
        self.hci_name = hci_name
        self.callback = callback
        self.running = True
        self.process: Optional[subprocess.Popen] = None

    def run(self):
        cmd = ["btmon", "-i", self.hci_name]
        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                bufsize=1,
            )

            current_frame_hex = []
            capturing = False

            while self.running and self.process.poll() is None:
                line = self.process.stdout.readline()
                if not line:
                    break
                
                # Check for advertising or HCI data packet lines
                clean = line.strip().lower()
                if "5d 4c" in clean:
                    # Found company ID signature in dump line
                    capturing = True
                    # Extract hex tokens from line
                    parts = clean.split()
                    hex_bytes = []
                    for p in parts:
                        if len(p) == 2:
                            try:
                                int(p, 16)
                                hex_bytes.append(p)
                            except ValueError:
                                pass
                    if hex_bytes:
                        raw = bytes.fromhex("".join(hex_bytes))
                        if self.callback:
                            self.callback(raw)

        except Exception as e:
            pass

    def stop(self):
        self.running = False
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=1.0)
            except Exception:
                self.process.kill()

