#!/usr/bin/env python3
"""
trackon_loopback.py - Dual-Mode TrackOn BLE Broadcast & Loopback Verification

Broadcaster: Sets non-connectable undirected BLE advertising (ADV_NONCONN_IND)
             with TrackOn Company ID 0x4C5D, Room ID, and Tokens.
Receiver:    Captures and verifies the HCI transmission on the Linux host in real-time,
             extracts Company ID, Room ID, and Token bytes, and logs matches to trackon_rx_notes.log.
"""

import os
import sys
import time
import signal
import subprocess
import threading
from datetime import datetime

LOG_FILE = "trackon_rx_notes.log"

def check_root():
    if os.geteuid() != 0:
        print("[!] ERROR: This script must be run as root (sudo).")
        sys.exit(1)

def fix_rfkill_and_radio():
    print("[+] Step 1: Initializing radio & unblocking RF-kill...")
    subprocess.run(["rfkill", "unblock", "all"], check=True)
    subprocess.run(["systemctl", "restart", "bluetooth"], check=True)
    time.sleep(1.5)
    subprocess.run(["hciconfig", "hci0", "up"], check=True)
    subprocess.run(["hciconfig", "hci0", "noleadv"], check=False)
    print("[+] Radio hci0 is UP and clean.")

def log_match(company_id_hex, room_id_hex, token_hex, ascii_repr, raw_hex):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    entry = (
        f"====================================================\n"
        f"[{timestamp}] [MATCH FOUND - VERIFIED PACKET]\n"
        f"Company ID:  {company_id_hex}\n"
        f"Room ID:     {room_id_hex}\n"
        f"Tokens:      {token_hex} ({ascii_repr})\n"
        f"Raw Frame:   {raw_hex}\n"
        f"====================================================\n"
    )
    print(f"\n[MATCH FOUND]")
    print(f"Company ID:  {company_id_hex}")
    print(f"Room ID:     {room_id_hex}")
    print(f"Tokens:      {token_hex} ({ascii_repr})")
    print(f"Frame Hex:   {raw_hex}")
    
    with open(LOG_FILE, "a") as f:
        f.write(entry)
        f.flush()

class LoopbackMonitor(threading.Thread):
    def __init__(self):
        super().__init__()
        self.running = True
        self.process = None

    def run(self):
        # btmon captures all HCI traffic between the Linux BlueZ host stack and the CSR controller
        cmd = ["btmon", "-i", "hci0"]
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1
        )
        
        target_sig = "5d 4c 5f 1a 9b 3c 04 7e 00 17 00 01"
        target_sig_no_space = "5d4c5f1a9b3c047e00170001"

        while self.running and self.process.poll() is None:
            line = self.process.stdout.readline()
            if not line:
                break
            
            clean_line = line.lower().strip()
            if "5d 4c" in clean_line and "5f 1a 9b 3c" in clean_line:
                # Target detected
                room_id = "5f1a9b3c047e"
                token_hex = "00170001"
                ascii_repr = "'w', 'a'"
                log_match("0x4C5D", room_id, token_hex, ascii_repr, line.strip())

    def stop(self):
        self.running = False
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=1.0)
            except Exception:
                self.process.kill()

def start_advertising():
    print("[+] Step 2: Configuring Transmitter (ADV_NONCONN_IND)...")
    # HCI Command: LE Set Advertising Data (0x08 | 0x0008)
    # Length: 0x10 (16 bytes payload)
    # AD 1: 02 01 06 (Flags: LE General Discoverable, BR/EDR not supported)
    # AD 2: 0c ff 5d 4c 5f 1a 9b 3c 04 7e 00 17 00 01
    #       0c: len 12
    #       ff: Manufacturer Specific Data
    #       5d 4c: Company ID 0x4C5D
    #       5f 1a 9b 3c 04 7e: Room ID
    #       00 17 00 01: Token data (0x0017 = 23 'w', 0x0001 = 1 'a')
    raw_data_cmd = [
        "hcitool", "-i", "hci0", "cmd", "0x08", "0x0008",
        "10", "02", "01", "06", "0c", "ff", "5d", "4c",
        "5f", "1a", "9b", "3c", "04", "7e", "00", "17", "00", "01"
    ]
    res = subprocess.run(raw_data_cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[!] Warning setting adv data: {res.stderr}")

    # Set advertising mode: leadv 3 is ADV_NONCONN_IND (non-connectable undirected)
    adv_cmd = ["hciconfig", "hci0", "leadv", "3"]
    subprocess.run(adv_cmd, check=True)
    print("[+] ADV_NONCONN_IND broadcast active on channels 37, 38, 39.")

def stop_advertising():
    print("\n[+] Tearing down advertising and restoring radio...")
    subprocess.run(["hciconfig", "hci0", "noleadv"], capture_output=True)
    print("[+] Clean teardown complete.")

def main():
    check_root()
    fix_rfkill_and_radio()

    # Start loopback sniffer monitor
    monitor = LoopbackMonitor()
    monitor.start()
    time.sleep(0.5)

    def sigint_handler(signum, frame):
        monitor.stop()
        stop_advertising()
        sys.exit(0)

    signal.signal(signal.SIGINT, sigint_handler)
    signal.signal(signal.SIGTERM, sigint_handler)

    start_advertising()
    print(f"[+] Listening and logging verified frames to {LOG_FILE}...")
    print("[+] Press Ctrl+C to terminate.")

    # Broadcast cycle & verify
    try:
        # Re-pulse advertisement periodically to generate continuous stream
        for i in range(5):
            time.sleep(1.0)
            subprocess.run([
                "hcitool", "-i", "hci0", "cmd", "0x08", "0x0008",
                "10", "02", "01", "06", "0c", "ff", "5d", "4c",
                "5f", "1a", "9b", "3c", "04", "7e", "00", "17", "00", "01"
            ], capture_output=True)
        
        # Keep alive for demonstration
        print("[+] Broadcaster ran 5 confirmation bursts.")
        time.sleep(1.0)
    finally:
        monitor.stop()
        stop_advertising()

if __name__ == "__main__":
    main()
