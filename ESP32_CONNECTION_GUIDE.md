# ESP32 to Web Dashboard Connection Guide
## Complete Step-by-Step Instructions

---

## 🎯 What You Need to Do

To connect your ESP32 to the web dashboard and control it through the website, you need to:

1. **Set up the hardware** (ESP32 + sensors + actuators)
2. **Configure the software** (upload firmware to ESP32)
3. **Start the Django backend server**
4. **Connect ESP32 to WiFi**
5. **Access the web dashboard**
6. **Test the controls**

---

## 📋 Hardware Requirements Checklist

### Essential Components:
- [ ] **ESP32 Development Board** (ESP32-WROOM-32 or similar)
- [ ] **USB Cable** for programming ESP32
- [ ] **Capacitive Soil Moisture Sensor** (Analog output)
- [ ] **DHT22 Temperature & Humidity Sensor**
- [ ] **LDR Light Sensor** (Photoresistor)
- [ ] **5V Relay Module** (at least 2 channels)
- [ ] **12V Water Pump** (optional for testing)
- [ ] **12V Fan** (optional for testing)
- [ ] **LED Light** (optional for testing)
- [ ] **Breadboard and Jumper Wires**
- [ ] **Power Supply** (5V for ESP32, 12V for actuators)

### For Testing Without Actuators:
- [ ] **LEDs** (to simulate pump/fan/light)
- [ ] **220Ω Resistors** (for LED protection)
- [ ] **Breadboard** for easy connections

---

## 🔧 Hardware Setup

### Step 1: Basic Connections (Minimum for Testing)
```
ESP32 Pin → Component
─────────────────────────────
3.3V      → Soil Moisture VCC
GND       → Soil Moisture GND
GPIO34    → Soil Moisture AO

3.3V      → DHT22 VCC
GND       → DHT22 GND
GPIO32    → DHT22 DATA

3.3V      → LDR (one leg)
GND       → LDR (other leg via 10kΩ resistor)
GPIO35    → LDR middle connection

3.3V      → Relay Module VCC
GND       → Relay Module GND
GPIO26    → Relay IN1 (Pump)
GPIO25    → Relay IN2 (Fan)
GPIO27    → Relay IN3 (Light)
```

### Step 2: Testing Setup (Using LEDs)
```
Relay COM → LED positive (+)
Relay NO  → 220Ω resistor → GND
```

---

## 💻 Software Setup

### Step 1: Install Arduino IDE
1. Download Arduino IDE 2.0+ from [arduino.cc](https://www.arduino.cc/)
2. Install ESP32 Board Manager:
   - Open Arduino IDE
   - Go to File → Preferences
   - Add this URL to "Additional Board Manager URLs":
     ```
     https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
     ```
   - Go to Tools → Board → Boards Manager
   - Search for "ESP32" and install "ESP32 Arduino"

### Step 2: Install Required Libraries
In Arduino IDE, go to Tools → Manage Libraries and install:
- **ArduinoJson** (version 6.19+)
- **DHT sensor library** by Adafruit
- **ESP32AnalogRead**
- **Ticker**

### Step 3: Configure WiFi Credentials
Open `esp32_smart_irrigation.ino` and update these lines:
```cpp
// WiFi Configuration (Line 39-40)
const char* ssid = "YOUR_WIFI_NAME";        // Change this
const char* password = "YOUR_WIFI_PASSWORD"; // Change this
```

### Step 4: Upload Firmware to ESP32
1. Connect ESP32 to computer via USB
2. In Arduino IDE:
   - Board: "ESP32 Dev Module"
   - Port: Select your ESP32 COM port
   - Upload the `esp32_smart_irrigation.ino` file
3. Open Serial Monitor (115200 baud) to see connection status

---

## 🌐 Backend Server Setup

### Step 1: Start Django Server
```bash
# Navigate to your project directory
cd f:/fullclone/agrosense.io

# Start the Django server
python manage.py runserver

# The server will start on http://127.0.0.1:8000
```

### Step 2: Test Backend API
Open your browser and test these URLs:
- http://127.0.0.1:8000/api/plant-profiles
- http://127.0.0.1:8000/api/devices

You should see JSON responses.

---

## 📡 ESP32 Connection Process

### Step 1: Power Up ESP32
1. Connect ESP32 to USB power
2. Open Arduino IDE Serial Monitor (115200 baud)
3. You should see:
   ```
   === Smart IoT Irrigation System Starting ===
   Connecting to WiFi.........
   WiFi connected successfully!
   IP address: 192.168.1.100
   System initialized successfully!
   Device ID: esp32_001
   Mode: MANUAL
   ```

### Step 2: Verify ESP32 Web Server
1. Find your ESP32's IP address from Serial Monitor
2. Open browser and go to: `http://[ESP32_IP]`
3. You should see the ESP32's built-in web interface

### Step 3: Test Sensor Readings
In Serial Monitor, you should see sensor data every 5 seconds:
```
Sensors - Soil: 45.2%, Temp: 23.5°C, Hum: 67.8%, Light: 350
Sensor data sent successfully
```

---

## 🌍 Access Web Dashboard

### Step 1: Open Main Dashboard
1. Open browser and go to: `http://127.0.0.1:8000/smart-irrigation-dashboard/`
2. You should see the beautiful glassmorphism dashboard

### Step 2: Select Device
1. In the "Select Device" dropdown, choose your ESP32
2. The dashboard should show live sensor data

### Step 3: Test Controls
1. **Manual Mode**: Click the mode buttons to switch modes
2. **Device Controls**: Click pump/fan/light buttons to control devices
3. **Plant Profiles**: Select different plants for automatic control

---

## 🧪 Testing Guide

### Test 1: Basic Connectivity
```bash
# Check if ESP32 is sending data
# Look in Serial Monitor for:
"Sensor data sent successfully"
```

### Test 2: Manual Control
1. On web dashboard, click "Pump ON"
2. Check Serial Monitor for control commands
3. Verify relay/LED responds

### Test 3: Automatic Mode
1. Switch to "Automatic Mode"
2. Change sensor values (e.g., dry soil)
3. Verify automatic device activation

### Test 4: Plant-Based Mode
1. Select "Plant-Based Mode"
2. Choose "Tomato" from plant profiles
3. Verify optimal conditions are maintained

---

## 🔧 Troubleshooting

### Problem: ESP32 Won't Connect to WiFi
**Symptoms**: Serial Monitor shows "Failed to connect to WiFi"
**Solutions**:
1. Check WiFi credentials in code
2. Verify WiFi network is 2.4GHz (ESP32 doesn't support 5GHz)
3. Move ESP32 closer to router
4. Restart ESP32

### Problem: No Sensor Data on Dashboard
**Symptoms**: Dashboard shows "--" for sensor values
**Solutions**:
1. Check ESP32 Serial Monitor for sensor readings
2. Verify sensor connections
3. Check Django server is running
4. Verify ESP32 is sending data (look for "Sensor data sent successfully")

### Problem: Controls Not Working
**Symptoms**: Clicking buttons doesn't change device states
**Solutions**:
1. Verify relay connections
2. Check if ESP32 receives commands (Serial Monitor)
3. Test with LEDs instead of actual actuators
4. Verify relay module power (5V)

### Problem: Backend API Not Responding
**Symptoms**: API endpoints return errors
**Solutions**:
1. Restart Django server
2. Check if port 8000 is available
3. Verify URLs are correct
4. Check Django logs for errors

---

## 📱 Mobile Access

### Access on Phone/Tablet
1. Ensure your phone is on the same WiFi network as the computer
2. Find your computer's IP address:
   - Windows: Open Command Prompt, type `ipconfig`
   - Mac: Open Terminal, type `ifconfig`
3. On your phone, go to: `http://[COMPUTER_IP]:8000/smart-irrigation-dashboard/`

### Remote Access (Advanced)
For remote access from anywhere:
1. Set up port forwarding on your router
2. Use a dynamic DNS service
3. Configure firewall rules
4. Use HTTPS for security

---

## 🚀 Quick Start Summary

### For Immediate Testing (Minimum Setup):
1. **Hardware**: ESP32 + 1 sensor (soil moisture) + 1 LED
2. **Software**: Upload firmware with your WiFi credentials
3. **Backend**: Start Django server (`python manage.py runserver`)
4. **Connect**: Power ESP32, wait for WiFi connection
5. **Control**: Open dashboard and test controls

### For Full System:
1. **Complete hardware setup** with all sensors and actuators
2. **Configure plant profiles** for your specific crops
3. **Test all three control modes**
4. **Set up mobile access** for remote monitoring
5. **Deploy in your garden/farm**

---

## 🎯 Success Indicators

You'll know everything is working when you see:

✅ **ESP32 Serial Monitor**:
```
WiFi connected successfully!
IP address: 192.168.1.100
Sensors - Soil: 45.2%, Temp: 23.5°C, Hum: 67.8%, Light: 350
Sensor data sent successfully
```

✅ **Web Dashboard**:
- Live sensor data updating every 5 seconds
- Control buttons responding immediately
- Mode switching working correctly
- Plant profiles loading properly

✅ **Device Control**:
- Relays clicking when buttons are pressed
- LEDs/actuators turning on/off
- Automatic control working in AUTO/PLANT modes

---

## 📞 Need Help?

If you encounter issues:

1. **Check Serial Monitor** first - it shows all ESP32 activity
2. **Verify hardware connections** - loose wires cause most problems
3. **Test with minimal setup** - start with just ESP32 + 1 sensor
4. **Check Django logs** - backend errors appear there
5. **Review this guide** - most solutions are covered above

The system is designed to be robust and will continue working even if some components fail. Start simple and build up to the full system!

---

**Ready to get started? Begin with Step 1: Hardware Setup, and you'll have your ESP32 connected to the web dashboard in no time! 🚀**
