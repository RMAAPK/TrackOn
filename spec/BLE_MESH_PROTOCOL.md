# TrackOn Protocol (TOP) Specification

**Version:** 1.0.0-DRAFT  
**License:** [MIT Educational License](LICENSE)  
**Classification:** Open Physical Hardware & Mesh Networking Topology  
**Authors:** TrackOn Open Protocol Community / Contributors

---

## 1. Ethical Stance, Neutrality & Liability Disclaimer

TrackOn is an **open-source communications protocol and hardware topology specification**, analogous to TCP/IP, 802.11 Wi-Fi, or Bluetooth. It is licensed strictly under the permissive **MIT License**.

> [!CAUTION]
> **Zero Liability & Anti-Stalking Policy**  
> The authors, maintainers, contributors, and copyright holders of the TrackOn specification, software, firmware, and hardware designs assume **ZERO LIABILITY** for the physical deployment, misuse, or application of this technology by third parties.
> 
> - **Prohibited Applications:** Deploying any physical beacon, sticker, or tag on an individual, vehicle, or private asset without the explicit, informed, and documented consent of the owner constitutes non-consensual surveillance ("stalking") and is strictly condemned.
> - **Protocol Transparency:** To mitigate abuse, the TrackOn protocol mandates open unencrypted beacon discovery frames (`TOP_ADV_DISC`) allowing any third-party smartphone, scanner, or operating system (iOS, Android, Linux) to immediately detect, warn, and locate nearby unassociated tracking stickers.

---

## 2. Core Design Objectives

1. **Passive / Semi-Passive Form Factor:** Ultra-thin adhesive flex-PCB sticker ($\le 0.55\text{ mm}$ total package) or credit-card footprint.
2. **Zero Bulky Modems:** No GPS receiver, no cellular modem, no SIM card slot, and no recurring carrier subscription costs.
3. **Decentralized Multi-Hop Mesh (Managed Flooding):** Nodes route packets cooperatively across industrial floors, workshops, warehouses, and physical asset rings.
4. **Content-Addressed Transport:** Seamlessly packages telemetry, sensor state, and IPFS CIDs into standard 2.4 GHz PHY frames.

---

## 3. Protocol Architecture (Layered Model)

```
┌────────────────────────────────────────────────────────────┐
│ 5. Application Layer                                       │
│    - Asset Telemetry (ForgeAI Industrial Health, Spindle)  │
│    - Content-Addressed CIDs (IPFS Encrypted Vault Links)   │
│    - Open Anti-Stalking Beacon Broadcast                   │
├────────────────────────────────────────────────────────────┤
│ 4. Transport & Security Layer                              │
│    - Noise Protocol Framework (Curve25519 + AES-256-GCM)   │
│    - Ephemeral Public Key Rotation (15-Minute Windows)     │
├────────────────────────────────────────────────────────────┤
│ 3. Network & Routing Layer (TOP-Mesh)                      │
│    - Managed Flooding & Time-To-Live (TTL = 7 hops)        │
│    - Monotonic Sequence Replay Protection                  │
├────────────────────────────────────────────────────────────┤
│ 2. Data Link Layer                                         │
│    - 32-bit Network Message Integrity Check (MIC)          │
│    - Low-Power Node (LPN) & Friend Node Synchronization    │
├────────────────────────────────────────────────────────────┤
│ 1. Physical Layer (PHY)                                    │
│    - 2.4 GHz BLE Channels (37, 38, 39)                     │
│    - 13.56 MHz Resonant Inductive Power Harvesting (NFC/HF)│
└────────────────────────────────────────────────────────────┘
```

---

## 4. Packet Structures

### 4.1 Unassociated Discovery Beacon (Anti-Stalking Compliance)
To prevent clandestine tracking, tags continuously broadcast a standardized open discovery frame that any receiver can inspect:

```c
typedef struct {
    uint8_t  len;            // Frame length
    uint8_t  ad_type;        // 0xFF (Manufacturer Specific)
    uint16_t cid;            // Company Identifier / Protocol Magic (0x544F 'TO')
    uint8_t  proto_ver;      // 0x01 (Version 1)
    uint8_t  tag_type;       // 0x01 = Adhesive Sticker, 0x02 = Wallet Card
    uint8_t  status_flags;   // Bit 0: Moving, Bit 1: Low Battery, Bit 2: Unpaired
    uint8_t  public_id[16];  // Ephemeral, rotating non-reversible identity token
} top_discovery_frame_t;
```

### 4.2 Multi-Hop Mesh PDU
For authorized peer-to-peer telemetry within asset networks (e.g. machine shops, tool cribs):

```c
typedef struct {
    uint8_t  ttl : 7;        // Max 7 hops
    uint8_t  ctl : 1;        // Control vs. Data PDU
    uint32_t sequence_id;    // Anti-replay 24-bit counter
    uint16_t src_node;       // Mesh Unicast Source
    uint16_t dst_group;      // Mesh Multicast / Group Address
    uint8_t  encrypted_body[16]; // Encrypted payload
    uint32_t mic32;          // AES-CMAC Network Message Integrity Check
} top_mesh_pdu_t;
```

---

## 5. Contributing & Pull Requests
Pull Requests (PRs), RFCs, and hardware designs are welcome from the global open-source community. All contributions become part of the public domain under the terms of the project's [MIT License](LICENSE).
