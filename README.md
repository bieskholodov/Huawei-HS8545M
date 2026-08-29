# Huawei WAP Control (HS8545M)


🌞 **Huawei WAP Control** is a custom component for Home Assistant that allows you to fully monitor, track, and manage your **Huawei HS8545M** WAP/ONT router via Telnet protocol. 🌐

---

## 🚀 Features

When installed, this integration automatically sets up a full diagnostic board for your Huawei router, splitting entities into controls, system telemetry, and presence detection:

### 🎮 Controls & Switches (`button` & `switch`)
* **Reboot Router** (`button.reboot_router`) — Remotely trigger a hardware `reset` of the router board via Telnet without accessing the web interface.
* **Update Data** (`button.update_data`) — Force an immediate poll of all diagnostic sensors.
* **Diagnostic Mode (Red LED)** (`switch.diagnostic_mode`) — Intelligently toggle the router's red diagnostic LED indicator.

### 📊 System & Optical Diagnostics (`sensor`)
* **🌐 External IP Address** — Real-time tracking of your WAN external IP.
* **🧠 Memory Usage (%)** — Router RAM consumption analytics.
* **⚡ CPU Load (%)** — Processor utilization metrics.
* **🔌 Optical Voltage (V)** — Current voltage supplied to the fiber transceiver module.
* **🌡️ Optical Temperature (°C)** — Temperature monitoring of the fiber optic laser.
* **📉 Optical Rx Signal (dBm)** — Received signal strength indicator (RSSI) of your internet fiber line.
* **📈 Optical Tx Power (dBm)** — Transmitting signal power of the laser.

### 📱 Device Tracking & Presence Detection (`device_tracker`)
Automatically scans the router's internal connection tables to discover and track all connected Wi-Fi and Ethernet clients (smartphones, Tasmota switches, Debian servers, laptops). Perfect for accurate home **presence detection**!

---

## 🛠️ Configuration

Configuration is fully supported via the Home Assistant Frontend (UI) integration flow.

1. Navigate to **Settings** ➔ **Devices & Services**.
2. Click **+ Add Integration** in the bottom right corner.
3. Search for **Huawei WAP Control**.
4. Enter your router's IP address, username, and password.

> 💡 **Default Factory Credentials:**
> For many ISP-supplied Huawei HS8545M models, the default login data is:
> * **Username:** `root`
> * **Password:** `admin`

---

## 📦 Installation

### Method 1: HACS (Recommended)
1. Open **HACS** ➔ **Integrations**.
2. Click the three dots `⋮` in the top right corner and select **Custom repositories**.
3. Paste the repository URL: `https://github.com/bieskholodov/Huawei-HS8545M`
4. Choose **Integration** as the category and click **Add**.
5. Click **Download** on the Huawei WAP Control card.
6. **Restart** Home Assistant.

### Method 2: Manual
1. Download the latest release `.zip` or `.tar.gz` archive.
2. Extract and copy the `huawei_wap_tracker` folder into your Home Assistant `config/custom_components/` directory.
3. **Restart** Home Assistant.

---

## 📋 Entity Reference & Translation Keys

If you want to customize or automate using these entities, here is the registry mapping table:

| Entity Type | Object ID / Translation Key | Default English Name | Description |
| :--- | :--- | :--- | :--- |
| `button` | `update_data` | Huawei Router - Update data | Forces immediate Telnet poll |
| `button` | `reboot_router` | Huawei Router - Reboot router | Sends `reset` command via Telnet |
| `switch` | `diagnostic_mode` | Diagnostic mode (Red LED) | Toggles the diagnostic hardware LED |
| `sensor` | `external_ip` | External IP | Displays current WAN IP address |
| `sensor` | `memory_usage` | Memory usage | Displays RAM load percentage |
| `sensor` | `cpu_load` | CPU load | Displays CPU load percentage |
| `sensor` | `optic_voltage` | Optical voltage | Laser module power voltage |
| `sensor` | `optic_temperature` | Optical temperature | Fiber module laser temperature |
| `sensor` | `optic_rx_signal` | Optical Rx signal | Fiber connection line quality status |
| `sensor` | `optic_tx_power` | Optical Tx power | Outbound fiber connection signal |

---

## 🌐 Localization

The integration natively supports languages using the Home Assistant internal translation schema.
* 🇬🇧 English (`en.json`)
* 🇷🇺 Russian (`ru.json`)
---
## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
---
Transform your router management experience 🏠, and monitor your fiber line connection with **Huawei WAP Control** today!
