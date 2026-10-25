# RMAA TrackOn

![TrackOn Banner](./assets/banner.jpg)

<div align="center">
  <a href="https://www.producthunt.com/products/trackon?embed=true&utm_source=badge-featured&utm_medium=badge&utm_campaign=badge-trackon" target="_blank" rel="noopener noreferrer"><img alt="TrackOn - The 10mm open-source silicon tracking tag. | Product Hunt" width="250" height="54" src="https://api.producthunt.com/widgets/embed-image/v1/featured.svg?post_id=1269412&theme=neutral&t=1791122010420"></a>
</div>

> **The world's thinnest, open-source bare-die tracking tag & decentralized mesh ecosystem.** Built on custom RISC-V silicon, charging via 13.56 MHz resonant magnetic flux, and powered by an airgapped, serverless physical BLE mesh protocol.

[![GitHub Stars](https://img.shields.io/github/stars/RMAAPK/TrackOn?style=social)](https://github.com/RMAAPK/TrackOn)
[![Organization: RMAA Holdings](https://img.shields.io/badge/Organization-RMAA%20Holdings-purple.svg)](https://github.com/RMAAPK)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Topology: BLE Mesh](https://img.shields.io/badge/Topology-BLE%20Mesh%20Flooding-blue.svg)](spec/BLE_MESH_PROTOCOL.md)
[![Hardware: <= 0.55mm Flex](https://img.shields.io/badge/Form%20Factor-%E2%89%A4%200.55mm%20Flex-emerald.svg)]()

---

## 🚀 Unified Monorepo Architecture

TrackOn is maintained by **RMAA Holdings** as a complete, unified hardware and cryptographic communication ecosystem:

```text
TrackOn/
├── assets/                 # Product Hunt graphics, banners, and diagrams
├── backend/                # Next.js 15 + Supabase dashboard and cloud portals
├── chat-engine/            # Airgapped, serverless BLE mesh messaging engine (TrackOn Chat)
│   ├── src/                # HKDF derivation, ChaCha20 cipher, and SQLite state ledger
│   └── tests/              # 100% passing protocol and frame verification suite
├── firmware/               # Open-source C/C++ firmware & RISC-V digital core logic
│   └── src/                # Apple Find My (FMN) & Google Find My Device cryptography
├── hardware/               # KiCad schematics, coil geometries, COMSOL simulations, RTL
│   ├── rtl/                # Custom ASIC Verilog core
│   └── TrackOn.kicad_pcb   # 10x10mm flex-PCB layout
├── spec/                   # Protocol & Wire RFC documents
│   ├── BLE_MESH_PROTOCOL.md# 31-byte legacy PDU wire specifications
│   ├── dictionary_v1.json  # Pre-compiled 2-byte token coordinates
│   └── TRACKER_PROTOCOL.md # Micro-hardware proximity beaconing
├── verification/           # Empirical verification scripts & hardware capture logs
│   ├── trackon_loopback.py # Dual-mode Linux radio loopback broadcaster & sniffer
│   └── trackon_rx_notes.log# Live verified physical HCI packet captures
└── docs/                   # Architectural blueprints and whitepapers
    └── CHAT_ARCHITECTURE.md# End-to-end cryptographic and mesh topology spec
```

---

## ⚡ Core Pillars

1. **Custom Bare-Die Silicon & Flex Hardware (`hardware/`)**
   - Direct bare-die wirebonding on 25 µm Polyimide flexible printed circuit (FPC), keeping total thickness under 0.55 mm.
   - 13.56 MHz resonant inductive flux coil charging an ultra-thin 0.2 mm thin-film lithium pouch.
   - Eliminates bulky CR2032 coin cells (3.2 mm) and power-hungry GPS receivers.

2. **Airgapped BLE Mesh Chat & Data Transport (`chat-engine/`)**
   - Operates connectionless over unbonded 2.4 GHz Bluetooth advertising channels (`ADV_NONCONN_IND`).
   - Uses assigned silicon shard **Company ID `0x4C5D`** for hardware-level packet filtering with 0% CPU wake on mismatched traffic.
   - Encapsulates 48-bit room routing, monotonic sliding-window anti-replay counters, and tokenized dictionary coordinates inside strict 31-byte legacy frames.

3. **Multi-Tier Network Topologies (`spec/`)**
   - **Tier 1 (Real-Time Blanket):** Managed Flooding Mesh with stochastic jitter (20–150 ms) and SipHash deduplication.
   - **Tier 2 (Static Infrastructure):** Cluster-Tree Hybrid Backbone with anchor gateways.
   - **Tier 3 (Long-Distance Airgap):** Opportunistic Delay-Tolerant (DTN) store-and-forward.
   - **Tier 4 (Dedicated Tunneling):** Scatternet / Piconet bridging.

4. **Empirical Hardware Verification (`verification/`)**
   - Fully verified on bare-metal Linux radio hardware (`hci0`).
   - Captures and logs raw frame validation directly to disk:
   ```text
   [MATCH FOUND - VERIFIED PACKET]
   Company ID:  0x4C5D
   Room ID:     5f1a9b3c047e
   Tokens:      00170001 ('w', 'a')
   Raw Frame:   10 02 01 06 0c ff 5d 4c 5f 1a 9b 3c 04 7e 00 17
   ```

---

## ⚖️ Ethical Use & Zero-Liability Notice
TrackOn is licensed under the **[MIT License](LICENSE)**. 

- **Zero Stalking Tolerance:** Sticking an unconsented physical tracking tag onto an individual or personal property without permission is strictly illegal and fundamentally violates the ethical purpose of this project.
- **Mandatory Anti-Stalking Beaconing:** The firmware includes mandatory proximity discovery frames enabling any nearby Android, iOS, or Linux device to identify unassociated tags moving with them.

---

*© 2026 RMAA Holdings / RMAA Tech. All Rights Reserved.*
