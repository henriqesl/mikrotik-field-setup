# MikroTik Field Setup

Interactive and offline-first MikroTik RouterOS script generator for rapid Point-to-Point (PtP) and Point-to-Multipoint (PtMP) deployments.

Designed to help field technicians configure MikroTik radios quickly, consistently, and without typing errors.

---

# The Problem & Benefits

Configuring MikroTik radios manually through the CLI is slow and prone to mistakes, especially during field installations. This app allows technicians to input only the essential data (SSID, Password, IP, and Gateway) to instantly generate a standardized script.

**Key Benefits:**
- Faster deployments
- Reduced human errors
- Standardized ISP configurations
- Secure wireless settings
- 100% offline workflow

---

# Features

- **Dual Package Support:** Compatible with both legacy (`wireless`) and RouterOS v7 (`wifi`) stacks.
- **DFS Prevention:** Auto-suggests radar-free frequencies and standard channel widths (20/40 MHz) to avoid DFS wait periods.
- **Transparent Bridge Ready:** Standardized automation for PtP and PtMP setups.
- **Zero Dependencies:** A single HTML file that runs completely offline on Windows, Linux, macOS, Android, and iOS. No backend or database required.
- **One-Click Copy:** Instantly copy and paste directly into Winbox's New Terminal.

---

# Usage

1. Download and open `mikrotik-generator.html` in any modern browser (offline supported).
2. Select the operation mode (**Access Point** or **Station**).
3. Fill in the network details (**SSID, Password, IP, Gateway**).
4. Click **Copy Script**.
5. Paste into a factory-reset MikroTik terminal (**No Default Configuration**).

---

# Workflow

```text
Open App ➔ Fill Info ➔ Generate & Copy ➔ Paste in Winbox ➔ Done ✔
```

---

# Roadmap

- ✅ **v1 (Current):** Single HTML, offline support, AP/Station generator, dual package support, DFS suggestions.
- 🚧 **v2 (Next):** Project componentization (HTML/CSS/JS separation), improved UI, and GitHub Pages/Vercel deployment.
- 🚧 **v3:** Progressive Web App (PWA) migration with React/Vue, native installation, and full offline cache.
- 🚧 **v4:** Edge Router Templates (PPPoE, VLANs, WireGuard, DHCP, Static Routing, Firewall).

---

# Contributing

Contributions are always welcome! If you've encountered a real-world RF scenario that isn't currently covered, feel free to open an Issue or submit a Pull Request. Every contribution helps improve deployments for ISP technicians.

---

# Tech & License

**Built with:** HTML5, CSS3, Vanilla JavaScript, RouterOS CLI.

**License:** Released under the MIT License. Feel free to use, modify, and distribute.
