# Smart IoT Irrigation System - Complete Wiring Guide
## Hardware Setup & Installation Instructions

---

## 🔌 Required Hardware Components

### ESP32 Development Board
- **ESP32 DevKit** (ESP32-WROOM-32 or similar)
- **USB Cable** for programming and debugging
- **Power Supply**: 5V USB or 12V external

### Sensors
- **Capacitive Soil Moisture Sensor** (Analog output)
- **DHT22 Temperature & Humidity Sensor** (Digital output)
- **LDR Light Dependent Resistor** (Analog output)
- **Jumper Wires** (Male-to-Male, various colors)

### Actuators & Relays
- **5V 2-Channel Relay Module** (or 3x 1-Channel relays)
- **12V Water Pump** (submersible or irrigation pump)
- **12V Cooling Fan** (120mm PC fan or similar)
- **12V LED Grow Light** (with proper driver)

### Power Management
- **12V 5A DC Power Supply** (for pumps/fan/lights)
- **LM2596 Buck Converter** (12V→5V, 3A output)
- **DC Barrel Jack Adapter** (5.5mm×2.1mm)
- **Fuses**: 5A for 12V circuits, 3A for 5V circuits

### Wiring Materials
- **Breadboard** for prototyping
- **Jumper Wires**: 22AWG solid core
- **Heat Shrink Tubing**: for insulation
- **Wire Connectors**: Spade terminals, ring terminals
- **Multimeter**: for testing connections
- **Screwdriver Set**: Phillips and flathead
- **Wire Strippers**: 16-22 AWG

---

## 📋 Pin Configuration & Wiring Diagram

### ESP32 Pin Mapping
```
ESP32 Pin    │ Component           │ Connection Type │ Wire Color
────────────┼─────────────────────┼─────────────────┼─────────────
GPIO34      │ Soil Moisture      │ Analog Input   │ Yellow
GPIO35      │ LDR Sensor         │ Analog Input   │ Green
GPIO32      │ DHT22 Data        │ Digital I/O    │ Blue
GPIO26      │ Relay IN1 (Pump)   │ Digital Out    │ Red
GPIO25      │ Relay IN2 (Fan)    │ Digital Out    │ Orange
GPIO27      │ Relay IN3 (Light)  │ Digital Out    │ Brown
3V3         │ ESP32 Power        │ Power         │ White
GND          │ Ground             │ Common Ground  │ Black
```

### Complete Wiring Diagram
```
                    ┌─────────────────────────────────────────┐
                    │         12V 5A Power Supply        │
                    │    ┌────────────────────────────┐    │
                    │    │  LM2596 Buck Converter    │    │
                    │    │  (12V→5V, 3A)          │    │
                    │    │  +───┐                   │    │
                    │    │  │   │                   │    │
                    │    │  │   │                   │    │
     ┌────────────┴────┴────┴────┐ │   │   │                   │    │
     │ ESP32 Development Board        │   │   │                   │    │
     │  ┌─────────────────────┐       │   │   │                   │    │
     │  │  Soil Moisture     │       │   │   │                   │    │
     │  │  (GPIO34)         │       │   │   │                   │    │
     │  │  DHT22 (GPIO32)     │       │   │   │                   │    │
     │  │  LDR (GPIO35)       │       │   │   │                   │    │
     │  │  Relay Module       │       │   │   │                   │    │
     │  │  GPIO26 (Pump)     │       │   │   │                   │    │
     │  │  GPIO25 (Fan)      │       │   │   │                   │    │
     │  │  GPIO27 (Light)    │       │   │   │                   │    │
     │  └─────────────────────┘       │   │   │   │                   │    │
     │                               │   │   │   │                   │    │
     │ 5V Power Supply               │   │   │   │                   │    │
     │  ┌─────────────────────────┐       │   │   │   │                   │    │
     │  │ Relay Module       │       │   │   │                   │    │
     │  │  VCC → 5V        │       │   │   │                   │    │
     │  │  GND → GND        │       │   │   │                   │    │
     │  │  IN1 → GPIO26      │       │   │   │                   │    │
     │  │  IN2 → GPIO25      │       │   │   │                   │    │
     │  │  IN3 → GPIO27      │       │   │   │                   │    │
     │  └─────────────────────┘       │   │   │   │                   │    │
     │                               │   │   │   │                   │    │
     │  ┌─────────────────────────┐       │   │   │   │                   │    │
     │  │ High Power       │       │   │   │                   │    │
     │  │  Devices         │       │   │   │                   │    │
     │  │  ┌─────────────┐   │       │   │   │                   │    │
     │  │  │ Water Pump  │   │       │   │   │                   │    │
     │  │  │ 12V Input  │   │       │   │                   │    │
     │  │  │ COM → NO   │   │       │   │                   │    │
     │  │  └─────────────┘   │       │   │   │                   │    │
     │  │  ┌─────────────┐   │       │   │   │                   │    │
     │  │  │ Cooling Fan │   │       │   │                   │    │
     │  │  │ 12V Input  │   │       │   │                   │    │
     │  │  │ COM → NO   │   │       │   │                   │    │
     │  │  └─────────────┘   │       │   │   │                   │    │
     │  │  ┌─────────────┐   │       │   │   │                   │    │
     │  │  │ LED Light  │   │       │   │                   │    │
     │  │  │ 12V Input  │   │   │   │                   │    │
     │  │  │ COM → NO   │   │   │   │                   │    │
     │  │  └─────────────┘   │       │   │   │                   │    │
     │                               │   │   │   │                   │    │
     │  Common Ground (12V & 5V) │   │   │   │                   │    │
     │                               │   │   │   │                   │    │
     └───────────────────────────────┴───────┴───────┴───────┴───────┘
```

---

## 🔧 Assembly Instructions

### Step 1: ESP32 Setup
1. **Install Arduino IDE**
   - Download Arduino IDE 2.0+ from arduino.cc
   - Install ESP32 Board Manager: "ESP32 Arduino" by Espressif Systems
   - Select Board: "ESP32 Dev Module" or "DOIT ESP32 DEVKIT V1"

2. **Install Required Libraries**
   ```cpp
   # In Arduino IDE, install these libraries:
   - WiFi.h (built-in)
   - ArduinoJson.h (version 6.19+)
   - DHT sensor library by Adafruit
   - ESP32AnalogRead.h
   - Ticker.h
   ```

3. **Upload Firmware**
   - Open `esp32_smart_irrigation.ino` in Arduino IDE
   - Update WiFi credentials in the code
   - Select correct COM port and board
   - Upload firmware to ESP32

### Step 2: Sensor Connections
1. **Soil Moisture Sensor**
   - Connect VCC → 3.3V (ESP32)
   - Connect GND → GND (ESP32)
   - Connect AO → GPIO34 (Yellow wire)
   - Calibrate: Dry air = 0%, Water = 100%

2. **DHT22 Temperature/Humidity Sensor**
   - Connect VCC → 3.3V (ESP32)
   - Connect GND → GND (ESP32)
   - Connect DATA → GPIO32 (Blue wire)
   - Add 10kΩ pull-up resistor between VCC and DATA

3. **LDR Light Sensor**
   - Connect one leg → 3.3V (ESP32)
   - Connect other leg → GND (ESP32)
   - Connect middle leg → GPIO35 (Green wire)
   - Add 10kΩ resistor in series with LDR

### Step 3: Relay Module Setup
1. **Power Connections**
   - Connect VCC → 5V (from buck converter)
   - Connect GND → GND (common ground)
   - Verify 5V output with multimeter

2. **Control Signal Connections**
   - Connect IN1 → GPIO26 (Red wire) - Water Pump
   - Connect IN2 → GPIO25 (Orange wire) - Cooling Fan
   - Connect IN3 → GPIO27 (Brown wire) - LED Light
   - Test with multimeter: LOW = ON, HIGH = OFF

### Step 4: High Power Device Connections
1. **General Safety Rules**
   - **ALWAYS DISCONNECT POWER** before making connections
   - Use appropriate wire gauge (18-22 AWG for 12V devices)
   - Add fuses close to power source
   - Secure all connections with proper terminals

2. **Water Pump Connection**
   - Connect pump positive (+) → Relay COM terminal
   - Connect pump negative (-) → 12V power supply negative
   - Add 5A fuse in series with positive lead
   - Use waterproof connections for outdoor installation

3. **Cooling Fan Connection**
   - Connect fan positive (+) → Relay COM terminal
   - Connect fan negative (-) → 12V power supply negative
   - Add 1A fuse for protection
   - Verify fan rotation direction

4. **LED Grow Light Connection**
   - Connect light positive (+) → Relay COM terminal
   - Connect light negative (-) → 12V power supply negative
   - Add 1A fuse for protection
   - Use proper LED driver if required

---

## ⚡ Power Supply Setup

### LM2596 Buck Converter Configuration
```
LM2596 Pinout:
┌─────────────────┬─────────────────┐
│ Pin 1: VIN  │ 12V Input (+) │
│ Pin 2: GND  │ Ground          │
│ Pin 3: GND  │ Ground          │
│ Pin 4: VOUT │ 5V Output (+) │
└─────────────────┴─────────────────┘

Settings:
- Input Voltage: 12V DC
- Output Voltage: 5V DC
- Max Current: 3A
- Adjust potentiometer for precise 5V output
```

### Power Distribution
```
12V 5A Power Supply
├── 5A Main Fuse
├── LM2596 Buck Converter (12V→5V)
│   ├── 3A Fuse on 5V output
│   └── 5V for ESP32 + Relay Module
├── 12V Distribution Block
│   ├── 5A Fuse for Water Pump
│   ├── 1A Fuse for Cooling Fan
│   ├── 1A Fuse for LED Light
│   └── Individual switches for each device
└── Common Ground Bus
```

---

## 🔧 Testing & Calibration

### Sensor Testing
1. **Soil Moisture Sensor**
   ```
   // Test code snippet
   void testSoilMoisture() {
     int value = analogRead(SOIL_MOISTURE_PIN);
     int moisture = map(value, 0, 4095, 100, 0);
     Serial.printf("Raw: %d, Moisture: %d%%\n", value, moisture);
   }
   ```

2. **DHT22 Sensor**
   ```
   // Test code snippet
   void testDHT22() {
     float temp = dht.readTemperature();
     float hum = dht.readHumidity();
     if (!isnan(temp) && !isnan(hum)) {
       Serial.printf("Temp: %.1f°C, Hum: %.1f%%\n", temp, hum);
     } else {
       Serial.println("DHT22 read error");
     }
   }
   ```

3. **LDR Light Sensor**
   ```
   // Test code snippet
   void testLightSensor() {
     int value = analogRead(LDR_PIN);
     int light = map(value, 0, 4095, 0, 1000);
     Serial.printf("Raw: %d, Light: %d\n", value, light);
   }
   ```

### Relay Testing
```cpp
void testRelays() {
  Serial.println("Testing relays...");
  
  // Test each relay for 2 seconds
  digitalWrite(PUMP_RELAY_PIN, LOW);   // Turn ON
  Serial.println("Pump ON");
  delay(2000);
  digitalWrite(PUMP_RELAY_PIN, HIGH);  // Turn OFF
  Serial.println("Pump OFF");
  delay(1000);
  
  digitalWrite(FAN_RELAY_PIN, LOW);
  Serial.println("Fan ON");
  delay(2000);
  digitalWrite(FAN_RELAY_PIN, HIGH);
  Serial.println("Fan OFF");
  delay(1000);
  
  digitalWrite(LIGHT_RELAY_PIN, LOW);
  Serial.println("Light ON");
  delay(2000);
  digitalWrite(LIGHT_RELAY_PIN, HIGH);
  Serial.println("Light OFF");
}
```

---

## 🔐 Safety Precautions

### Electrical Safety
- **NEVER work on live circuits** - Always disconnect power first
- **Use proper insulation** on all 12V connections
- **Install fuses** close to power source (5A for main, 1A for devices)
- **Ground all equipment** properly to prevent shocks
- **Use appropriate wire gauge** for current ratings
- **Keep water away from electronics** to prevent short circuits

### Installation Safety
- **Mount in weatherproof enclosure** for outdoor use
- **Provide proper ventilation** for heat dissipation
- **Secure all connections** with vibration-resistant terminals
- **Label all wires and components** clearly
- **Keep emergency stop accessible** at all times

### Operational Safety
- **Install emergency stop button** physically accessible
- **Set maximum runtime limits** in firmware
- **Monitor temperature** and shutdown if overheating
- **Test all functions** before full deployment
- **Regular maintenance schedule** for reliability

---

## 📱 Mobile App Integration

### WiFi Configuration
```cpp
// WiFi Manager for ESP32
#include <WiFiManager.h>

WiFiManager wifiManager;

void setupWiFi() {
  wifiManager.setAPConfigModeTimeout(300);  // 3 minutes timeout
  wifiManager.setConfigPortalTimeout(180);     // 3 minutes portal
  
  // Custom parameters
  WiFiManagerParameter custom_mqtt_server("mqtt_server", "mqtt.broker.com");
  WiFiManagerParameter custom_device_id("device_id", "esp32_001");
  
  if (!wifiManager.autoConnect()) {
    Serial.println("Failed to connect and hit timeout");
    // Reset and try again
    ESP.restart();
  }
}
```

### MQTT Integration
```cpp
#include <PubSubClient.h>
#include <ArduinoJson.h>

WiFiClient espClient;
PubSubClient client(espClient);

void setupMQTT() {
  client.setServer("mqtt.broker.com", 1883);
  client.setCallback(mqttCallback);
  
  while (!client.connected()) {
    Serial.println("Connecting to MQTT...");
    if (client.connect("esp32_001")) {
      Serial.println("MQTT Connected");
      client.subscribe("agrosense/esp32_001/commands");
    }
    delay(1000);
  }
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  DynamicJsonDocument doc(256);
  deserializeJson(doc, payload);
  
  if (doc.containsKey("command")) {
    String command = doc["command"];
    executeCommand(command);
  }
}
```

---

## 🚀 Deployment Checklist

### Pre-Deployment Testing
- [ ] All sensors read correctly in Serial Monitor
- [ ] All relays respond to control commands
- [ ] WiFi connection stable and reliable
- [ ] MQTT connection working (if used)
- [ ] Emergency stop functions properly
- [ ] Power supply voltages correct (5V and 12V)
- [ ] Fuses installed and rated correctly

### Field Installation
- [ ] Weatherproof enclosure installed
- [ ] All connections insulated and protected
- [ ] Ground fault circuit installed
- [ ] Emergency stop button accessible
- [ ] Power supply protected from elements
- [ ] Cable management and strain relief
- [ ] Label all components clearly

### Software Configuration
- [ ] WiFi credentials configured
- [ ] Device ID set uniquely
- [ ] MQTT broker configured (if using)
- [ ] Sensor calibration completed
- [ ] Safety limits configured
- [ ] Update intervals set appropriately
- [ ] Error handling tested
- [ ] OTA updates configured

---

## 🔧 Troubleshooting Guide

### Common Issues & Solutions

#### 1. ESP32 Won't Connect to WiFi
**Problem**: ESP32 continuously restarts or can't connect
**Causes**: 
- Wrong WiFi credentials
- Weak signal strength
- Power supply issues
- Firmware bugs

**Solutions**:
- Verify SSID and password
- Move closer to router
- Check power supply voltage
- Add serial debugging output
- Reset ESP32 and try again

#### 2. Sensor Readings Incorrect
**Problem**: Wrong or erratic sensor values
**Causes**:
- Loose connections
- Power supply noise
- Sensor calibration issues
- Code bugs

**Solutions**:
- Check all wiring connections
- Add capacitors to power lines
- Calibrate sensors in known conditions
- Add debugging output
- Test with multimeter

#### 3. Relays Not Working
**Problem**: Relays don't respond to commands
**Causes**:
- Incorrect pin assignments
- Relay module power issues
- Code logic errors
- Hardware failures

**Solutions**:
- Verify pin connections
- Check relay module power (5V)
- Test with simple on/off code
- Check relay module with multimeter
- Replace faulty relay module

#### 4. Power Supply Issues
**Problem**: Devices not getting enough power
**Causes**:
- Undersized power supply
- Voltage drops in long wires
- Loose connections
- Multiple devices on same circuit

**Solutions**:
- Upgrade power supply capacity
- Use thicker wires for long runs
- Tighten all connections
- Measure voltage at device
- Add local capacitors

### Debug Mode
```cpp
#define DEBUG_MODE true

void setup() {
  Serial.begin(115200);
  
  #if DEBUG_MODE
  Serial.println("=== DEBUG MODE ENABLED ===");
  #endif
  
  // ... rest of setup
}

void loop() {
  #if DEBUG_MODE
  Serial.printf("Free Heap: %d, WiFi Status: %d\n", 
                ESP.getFreeHeap(), WiFi.status());
  #endif
  
  // ... rest of loop
}
```

---

## 📊 Performance Optimization

### Power Consumption
```
Device Power Usage:
ESP32 Development Board:    200mA @ 3.3V = 0.66W
DHT22 Sensor:           1.5mA @ 3.3V = 0.005W
Soil Moisture Sensor:     10mA @ 3.3V = 0.033W
LDR Light Sensor:         5mA @ 3.3V = 0.017W
Relay Module:           200mA @ 5V = 1.0W
Total Standby:          ~1.7W

Active Devices:
Water Pump (12V):        2A @ 12V = 24W
Cooling Fan (12V):       0.5A @ 12V = 6W
LED Grow Light (12V):     1A @ 12V = 12W
Total Active:             ~42W

System Efficiency:
- Standby: 1.7W continuous
- Active: 42W (when all devices on)
- Battery Life (with 10000mAh): ~5 hours standby
```

### Network Optimization
```cpp
// Efficient WiFi management
void manageWiFi() {
  static unsigned long lastWiFiCheck = 0;
  
  if (millis() - lastWiFiCheck > 60000) { // Check every minute
    if (WiFi.status() != WL_CONNECTED) {
      Serial.println("WiFi disconnected, attempting reconnect...");
      WiFi.reconnect();
    }
    lastWiFiCheck = millis();
  }
}

// Deep sleep for power saving
void enterDeepSleep() {
  if (currentMode == "AUTO" && !anyDeviceActive()) {
    Serial.println("Entering deep sleep...");
    ESP.deepSleep(30 * 1000000); // Sleep for 30 seconds
  }
}
```

---

This complete wiring guide provides all the information needed to successfully build, install, and deploy a professional Smart IoT Irrigation system with ESP32 integration and comprehensive safety features.
