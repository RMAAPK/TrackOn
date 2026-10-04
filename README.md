# RMAA TrackOn

![TrackOn Banner](https://via.placeholder.com/1200x400/0a0a0a/ffffff?text=RMAA+TrackOn+-+The+10mm+Silicon+Tracker)

> **The world's thinnest, open-source bare-die tracking tag.** Built on custom RISC-V silicon, charging via 13.56 MHz resonant magnetic flux, and natively integrated with the Apple Find My / Google Find My Device networks.

[![GitHub Stars](https://img.shields.io/github/stars/RMAAPK/TrackOn?style=social)](https://github.com/RMAAPK/TrackOn)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview
TrackOn is an ultra-low-profile (10x10mm, <= 0.55mm thick) flexible electronic tracking tag designed for high-density adhesion to everyday items (vape pods, tools, phone internals, personal gear). 

Instead of off-the-shelf bulky ICs, TrackOn uses a **custom in-house bare-die ASIC** running an RV32EC core. It ditches traditional batteries for a thin-film lithium pouch, kept alive indefinitely by tapping into ambient 13.56 MHz NFC/magnetic fields using a flexible Archimedean spiral coil.

## Core Pillars

1. **Custom Bare-Die Silicon (`hardware/rtl/`)**
   - RISC-V RV32EC digital core optimized for nano-ampere static power.
   - One-Time-Programmable (OTP) eFuse for burning elliptic curve root keys.
   - Strict Lithium Pouch PMU (Power Management Unit) ensuring 2.7V - 4.2V operating windows.

2. **Apple & Google Mesh Native (`firmware/src/`)**
   - Cryptographically compliant with Apple Find My Network (FMN) & Google Find My Device.
   - Rotating NIST P-224 Elliptic Curve Public Keys (changing every 15 minutes to prevent tracker-stalking).

3. **Cloud & Law Enforcement API (`backend/`)**
   - Next.js 15 + Supabase dashboard.
   - Sanitized `/v/:token` live-link endpoint for police, rendering real-time target coordinates and velocity vectors while stripping user PII.

---

### Product Hunt Pre-Launch
This repository contains the engineering blueprints, RTL stubs, firmware cryptography structures, and the Next.js portal scaffolding. We are building in public.

*© 2026 Ali CNC / RMAA Tech. All Rights Reserved.*
