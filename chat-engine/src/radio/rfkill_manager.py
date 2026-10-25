import subprocess
import time

class RadioManager:
    """Manages RF-kill state and BlueZ hci0 adapter lifecycle."""

    @staticmethod
    def initialize_adapter(hci_name: str = "hci0") -> bool:
        try:
            subprocess.run(["rfkill", "unblock", "all"], check=True, capture_output=True)
            subprocess.run(["systemctl", "restart", "bluetooth"], check=True, capture_output=True)
            time.sleep(1.5)
            subprocess.run(["hciconfig", hci_name, "up"], check=True, capture_output=True)
            subprocess.run(["hciconfig", hci_name, "noleadv"], capture_output=True)
            return True
        except Exception as e:
            print(f"[RadioManager] Initialization error: {e}")
            return False

    @staticmethod
    def teardown_adapter(hci_name: str = "hci0"):
        try:
            subprocess.run(["hciconfig", hci_name, "noleadv"], capture_output=True)
        except Exception:
            pass

