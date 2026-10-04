RMAA TrackOn — Hardware & Architecture Specification
Document ID: SPEC-RMAA-001
Classification: Proprietary / Engineering Blueprint
Target Platform: KiCad 8.x / Custom Polyimide Flex-PCB / RISC-V RTL / Supabase Backend
Author / Entity: Ali CNC / RMAA Tech

1. Executive Summary & Product Objective
RMAA TrackOn is a 10×10 mm ultra-low-profile, flexible electronic tracking tag designed for high-density adhesion to everyday items (vape pods, tools, phone internals, personal gear). It operates on a hybrid BLE 2.4 GHz crowd-mesh telemetry model, charges via 13.56 MHz resonant magnetic flux, and interfaces with a backend subscription platform featuring sanitized law-enforcement export links.

2. Electrical & Silicon Architecture
2.1 Silicon Layer (Bare-Die / WLCSP)
 * Compute Core: Open-source RV32EC RISC-V digital core synthesized for ultra-low static power.
 * Sleep / Active Budget:
   * Deep-sleep power: \le 1.8\ \mu\text{A} with real-time counter active.
   * Active beacon transmit pulse: \le 12\ \text{mA} peak at 0 dBm output power.
 * Transceiver: Integrated 2.4 GHz balanced direct-conversion RF front-end supporting Bluetooth Low Energy 5.x advertising frames (iBeacon / Eddystone compatible).
 * Power Management Unit (PMU): Integrated active MOSFET bridge rectifier and low-dropout (LDO) regulator accepting input voltages down to 0.8 V.

2.2 PCB & Substrate Specifications (KiCad Stackup)
 * Form Factor: 10.0 mm diameter circular or 10.0 × 10.0 mm square with 1.0 mm radius corners.
 * Total Assembly Profile: \le 0.55\ \text{mm} (excluding adhesive).
 * Layer Count: 2-Layer Flexible Printed Circuit (FPC).
 * Base Dielectric: 25 µm (1 mil) Polyimide core.
 * Copper Foil: 18 µm (1/2 oz) Rolled Annealed (RA) copper for fatigue resistance against mechanical bending.
 * Coverlay: 25 µm Polyimide with 25 µm flexible acrylic adhesive.
 * Trace / Space DRC Rules: 75 µm / 75 µm (3 mil / 3 mil) HDI limits. NSMD teardropped pads.
 * Routing Geometry: Arc / curved routing exclusively; zero 90° or 45° angular intersections.

2.3 Resonant Magnetic Harvesting (13.56 MHz)
 * Inductive Coil Design: Outer-perimeter planar Archimedean spiral scripted via KiCad pcbnew Python API.
 * Turn Count: 5 concentric turns on Layer 1 (Top Copper), 75 µm trace width, 75 µm gap. Layer-change via returning straight on Layer 2.
 * Magnetic Isolation Barrier: 0.05 mm flexible sintered ferrite sheet laminated on the bottom substrate to isolate the coil from metal surfaces (phones, pods, brass fixtures) and eliminate eddy-current parasitic losses.
 * Storage Cell: 0.2 mm solid-state thin-film lithium pouch or surface-mount ceramic supercapacitor array.

3. Firmware & Protocol Structure
3.1 Advertising Payload Frame
[ 0x02, 0x01, 0x06 ]                -> Flags (LE General Discoverable)
[ 0x1A, 0xFF ]                      -> Manufacturer Specific Data (26 bytes)
[ 0xAA, 0x01 ]                      -> RMAA System Identifier
[ 16-byte Device UUID ]             -> Cryptographic Unique Device Token
[ 2-byte Epoch Counter ]            -> Monotonic Rolling Increment
[ 1-byte Battery Level ]            -> Scaled 0–100%
[ 4-byte HMAC-SHA256 Truncated ]    -> Anti-spoofing signature

3.2 Operating States
 * Dormant / Shelf Mode: RF off, RTC watchdog monitoring magnetic charging circuit.
 * Standard Beacon Mode: 1 burst every 2500 ms (configurable via app).
 * Lost / Alarm Mode: 1 burst every 400 ms triggered by geofence failure or cloud toggle.

4. Software Stack & Infrastructure
                  ┌──────────────────────┐
                  │   RMAA TrackOn Tag   │
                  └──────────┬───────────┘
                             │ 2.4 GHz BLE Frame
                             ▼
                  ┌──────────────────────┐
                  │ Mobile App / Mesh    │
                  │ (React Native / iOS) │
                  └──────────┬───────────┘
                             │ HTTPS / TLS 1.3
                             ▼
                  ┌──────────────────────┐
                  │ Cloud API & Auth     │
                  │ (Next.js / Supabase) │
                  └────┬────────────┬────┘
                       │            │
         User Portal ──┘            └── Police Live Link

4.1 Cloud Backend (Supabase / PostgreSQL)
 * Database Tables:
   * devices: id, owner_id, mac_address_token, public_key, status, created_at
   * telemetry: id, device_id, latitude, longitude, accuracy_meters, rssi, battery_pct, timestamp
   * police_shares: token_hash, device_id, is_active, expires_at

4.2 Sanitized Law Enforcement Link Endpoint (/v/:token)
 * Strips all private user personal information, account history, and billing data.
 * Real-time self-updating map rendering target coordinates with confidence circles.
 * Shows UTC timestamps, velocity vector (if mobile), and signal RSSI strength indicator.

5. Intellectual Property & Brand Alignment
 * Primary Mark: RMAA TrackOn (Filed under Nice Class 9: Beacons, Electronic Tracking Tags, Telemetry Platforms).
 * Complementary Mark: Ali CNC (Retains manufacturing, machining, and industrial CAD/CAM scope).
 * Copyright Notice (UI & Firmware):
   © 2026 Ali CNC / RMAA Tech. All Rights Reserved. Firmware, KiCad PCB Layout, and Proprietary Schematics Protected.

6. Cursor Project Bootstrap Tasks
To begin implementation in Cursor immediately, execute in sequence:
 * hardware/: Initialize KiCad 8 workspace with custom 10×10 mm circular edge cut and FPC design rules. Run Python script to generate the 13.56 MHz planar spiral coil footprint.
 * firmware/: Setup C/C++ project for low-power RISC-V / BLE advertising stack with sleep timer hooks and payload encryption.
 * backend/: Initialize Next.js 15 + Supabase schema matching the telemetry and sanitized police-sharing tables outlined above.
