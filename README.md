# Huawei-HS8545M

# Huawei WAP Control (HS8545M)

Custom integration for Home Assistant to monitor and control Huawei HS8545M WAP/ONT routers. This integration tracks connected devices, monitors optical signal levels, router system load, and provides remote management actions.

## Features

### 🎮 Controls & Switches
* **Reboot Router** (`button`) — Remotely restart your Huawei router from Home Assistant.
* **Update Data** (`button`) — Force immediate poll of all diagnostic data.
* **Diagnostic Mode (Red LED)** (`switch`) — Toggle diagnostic LED state.

### 📊 System & Optical Sensors
* **External IP Address** — Monitors your WAN IP.
* **CPU Load (%)** — Real-time router processor utilization.
* **Memory Usage (%)** — Router RAM consumption.
* **Optical Tx Power (dBm)** — Transmitting power of the fiber optic module.
* **Optical Rx Signal (dBm)** — Received signal strength indicator (RSSI) for your fiber line.
* **Optical Voltage (V)** — Voltage of the optical transceiver.
* **Optical Temperature (°C)** — Temperature monitoring for the fiber module.

### 📱 Device Tracking (Presence Detection)
Automatically discovers and tracks all connected Wi-Fi and Ethernet devices (e.g., smartphones, laptops, IoT smart plugs, Tasmota/Debian servers) for home presence detection (`device_tracker`).

---

## Installation

### Method 1: HACS (Recommended)
1. Ensure **HACS** is installed in your Home Assistant.
2. Go to **HACS** ➔ **Integrations**.
3. Click the three dots `⋮` in the top right corner and select **Custom repositories**.
4. Paste the repository URL: `https://github.com`
5. Select **Integration** as the category and click **Add**.
6. Find **Huawei WAP Control** in the list and click **Download**.
7. **Restart** Home Assistant.

### Method 2: Manual Installation
1. Download the latest release archive.
2. Copy the `huawei_wap_tracker` folder from `custom_components/` into your Home Assistant `config/custom_components/` directory.
3. **Restart** Home Assistant.

---

## Configuration

1. In Home Assistant, navigate to **Settings** ➔ **Devices & Services**.
2. Click **+ Add Integration** in the bottom right corner.
3. Search for **Huawei WAP Control** and follow the on-screen setup flow to enter your router's credentials.

> 💡 **Default Credentials:** For many Huawei HS8545M models, the default login data is:
> * **Username:** `root`
> * **Password:** `admin`
