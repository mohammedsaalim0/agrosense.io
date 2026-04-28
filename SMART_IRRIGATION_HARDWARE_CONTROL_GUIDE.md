# Smart Irrigation Hardware Control - Complete Guide

## 🔧 How Smart Irrigation Controls Hardware

### System Architecture Overview
```
Web Dashboard → Django Backend → MQTT Broker → ESP32 → Hardware Components
     ↓              ↓              ↓           ↓           ↓
   User Interface  →  API Calls  →  Commands  →  GPIO Pins  →  Physical Devices
```

### Control Flow Mechanism

#### 1. User Interface → Backend
- User clicks "Water Now" on web dashboard
- JavaScript sends POST request to `/api/irrigation/water-now/`
- Django view processes the request

#### 2. Backend → MQTT Broker
- Django publishes MQTT message: `{"command": "start_pump"}`
- Topic: `agrosense/irrigation/esp32_001/command`
- Message routed through MQTT broker

#### 3. MQTT Broker → ESP32
- ESP32 subscribes to command topic
- Receives JSON command via MQTT
- Parses and executes hardware control

#### 4. ESP32 → Hardware Control
- Sets GPIO26 HIGH (activates relay)
- Relay closes circuit to 12V water pump
- Water pump starts irrigating

## 🛠️ Required Components List

### Core Components
1. **ESP32 Development Board** - $8-12
   - Model: ESP32-DevKitC or ESP32-WROOM-32
   - Voltage: 3.3V logic, 5V tolerant inputs
   - WiFi: 802.11 b/g/n
   - GPIO: 36 programmable pins

2. **Capacitive Soil Moisture Sensor** - $3-5
   - Model: Capacitive Soil Moisture Sensor V1.2
   - Voltage: 3.3V-5V DC
   - Output: Analog (0-3.3V)
   - Range: 0-100% moisture
   - Advantage: No corrosion, long lifespan

3. **5V Relay Module** - $2-3
   - Model: SRD-05VDC-SL-C Single Channel
   - Trigger Voltage: 5V DC
   - Load Capacity: 250V AC 10A / 30V DC 10A
   - Isolation: Opto-isolated
   - Input: 3.3V-5V compatible

4. **12V DC Water Pump** - $5-8
   - Type: Submersible mini pump
   - Voltage: 12V DC
   - Flow Rate: 3-5 liters/minute
   - Power: 3-5W
   - Connections: Standard hose fittings

5. **12V Power Supply** - $5-7
   - Input: 100-240V AC
   - Output: 12V DC 2A
   - Connector: 5.5mm barrel jack
   - Purpose: Power pump and relay

### Optional Components
- **DHT11 Sensor** - $2 (Temperature/Humidity)
- **Water Flow Sensor** - $3 (Water usage monitoring)
- **Solar Panel + Battery** - $25-50 (Off-grid power)
- **Waterproof Enclosure** - $10 (Weather protection)

## 🔌 Detailed Connection Instructions

### ESP32 Pin Layout Reference
```
ESP32 Board Pinout:
┌─────────────────────────────────────┐
│  EN  36  39  34  35  32  33  25  26  │
│  27  14  12  GND 13  SD2  SD3  CMD  │
│  5V  3V3  GND  TX0  RX0  D21  D19  D18│
│  D5   D6   D7   D8   D9   D10  D11  D12│
│  GND  VIN  3V3  GND  D13  SHD/SHD  SWP│
└─────────────────────────────────────┘
```

### Step-by-Step Wiring

#### Step 1: Soil Moisture Sensor Connection
```
Soil Moisture Sensor    →    ESP32
─────────────────────────────────────────
VCC (Red wire)          →    3V3 (Pin 1)
GND (Black wire)        →    GND (Pin 3)
AO (Analog Out)         →    GPIO34 (Pin 4)
```

#### Step 2: Relay Module Connection
```
Relay Module            →    ESP32
─────────────────────────────────────────
VCC                     →    5V (Pin 2)
GND                     →    GND (Pin 3)
IN (Signal)             →    GPIO26 (Pin 8)
```

#### Step 3: Water Pump Connection
```
Water Pump              →    Relay Module
─────────────────────────────────────────
+12V (Red wire)         →    COM (Common)
Ground (Black wire)     →    NC (Normally Closed)
```

#### Step 4: Power Supply Connection
```
12V Power Adapter       →    System
─────────────────────────────────────────
+12V Output             →    Relay COM + Pump +
Ground                  →    Relay NC + Pump -
```

### Complete Wiring Diagram
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   ESP32 Board   │     │  Relay Module   │     │   Water Pump    │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ 3V3 ────────┐   │     │  VCC ────────┐   │     │  +12V ────────┐ │
│ GND ────────┼───┼─────│  GND ────────┼───┼─────│  GND ────────┼─┘
│ GPIO34 ─────┘   │     │  IN ────────┐   │     │                 │
│                 │     │             │   │     │                 │
│ GPIO26 ─────────┼─────│  COM ───────┼───┼─────│  +12V ────────┐ │
│                 │     │  NC ────────┘   │     │  GND ────────┼─┘
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                │
┌─────────────────┐     ┌─────────────────┐
│  Soil Moisture  │     │  12V Power      │
│     Sensor      │     │    Adapter      │
├─────────────────┤     ├─────────────────┤
│ VCC ────────┐   │     │  +12V ────────┐ │
│ GND ────────┼───┼─────│  GND ────────┼─┘
│ AO ─────────┘   │     │                 │
└─────────────────┘     └─────────────────┘
        │
        └─────────────────┐
                          │
                          ▼
                   ┌─────────────────┐
                   │   ESP32 3V3     │
                   └─────────────────┘
```

## 💻 ESP32 Code for Hardware Control

### Pin Definitions
```cpp
// Pin Definitions
#define SOIL_MOISTURE_PIN 34    // ADC1_CH6 - Soil moisture sensor
#define RELAY_PIN 26           // GPIO26 - Relay control
#define PUMP_LED_PIN 2         // Built-in LED - Pump status indicator
```

### Sensor Reading Function
```cpp
int readSoilMoisture() {
    // Read analog value from soil moisture sensor
    int rawValue = analogRead(SOIL_MOISTURE_PIN);
    
    // Convert ADC value to percentage (0-100%)
    // Calibration values may need adjustment based on your soil
    int moisturePercent = map(rawValue, 2800, 1200, 0, 100);
    moisturePercent = constrain(moisturePercent, 0, 100);
    
    return moisturePercent;
}
```

### Pump Control Functions
```cpp
void startPump() {
    digitalWrite(RELAY_PIN, HIGH);    // Activate relay
    digitalWrite(PUMP_LED_PIN, HIGH); // Turn on LED indicator
    Serial.println("💧 Pump started - Irrigation active");
}

void stopPump() {
    digitalWrite(RELAY_PIN, LOW);     // Deactivate relay
    digitalWrite(PUMP_LED_PIN, LOW);  // Turn off LED indicator
    Serial.println("🚫 Pump stopped - Irrigation paused");
}
```

### MQTT Command Processing
```cpp
void mqttCallback(char* topic, byte* payload, unsigned int length) {
    Serial.print("📨 MQTT Command received: ");
    Serial.println(topic);
    
    // Parse JSON command
    DynamicJsonDocument doc(256);
    deserializeJson(doc, payload);
    
    String command = doc["command"];
    
    // Execute hardware control based on command
    if (command == "start_pump") {
        startPump();
        sendStatusUpdate(); // Report back to server
        
    } else if (command == "stop_pump") {
        stopPump();
        sendStatusUpdate(); // Report back to server
        
    } else if (command == "get_status") {
        sendStatusUpdate(); // Send current status
    }
}
```

## 🌐 Web-to-Hardware Communication Flow

### 1. User Action (Web Interface)
```javascript
// User clicks "Water Now" button
async function waterNow() {
    try {
        const response = await fetch('/api/irrigation/water-now/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        
        if (response.ok) {
            showToast('Watering command sent!', 'success');
        }
    } catch (error) {
        showToast('Error sending command', 'error');
    }
}
```

### 2. Django Backend Processing
```python
@csrf_exempt
def irrigation_water_now_api(request):
    if request.method == 'POST':
        try:
            # Send MQTT command to ESP32
            device_id = "esp32_001"
            command = {
                "command": "start_pump",
                "timestamp": timezone.now().isoformat()
            }
            
            # Publish via MQTT
            mqtt_manager.send_command(device_id, command)
            
            return JsonResponse({
                'status': 'success',
                'message': 'Watering command sent to device'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
```

### 3. MQTT Message Transmission
```python
class MQTTManager:
    def send_command(self, device_id, command):
        topic = f"agrosense/irrigation/{device_id}/command"
        message = json.dumps(command)
        
        # Publish to MQTT broker
        self.client.publish(topic, message)
        print(f"📡 Command sent to {device_id}: {command}")
```

### 4. ESP32 Hardware Execution
```cpp
void setup() {
    // Initialize hardware pins
    pinMode(RELAY_PIN, OUTPUT);
    pinMode(PUMP_LED_PIN, OUTPUT);
    digitalWrite(RELAY_PIN, LOW);  // Start with pump OFF
    
    // Connect to WiFi and MQTT
    setupWiFi();
    setupMQTT();
}

void loop() {
    // Maintain MQTT connection
    if (!client.connected()) {
        reconnectMQTT();
    }
    client.loop();  // Process incoming MQTT messages
    
    // Read sensor data periodically
    static unsigned long lastSensorRead = 0;
    if (millis() - lastSensorRead > 5000) {  // Every 5 seconds
        updateSensorData();
        lastSensorRead = millis();
    }
}
```

## 🔧 Hardware Control Mechanisms

### Relay Control Logic
```cpp
void controlRelay(bool turnOn) {
    if (turnOn) {
        digitalWrite(RELAY_PIN, HIGH);  // Close relay circuit
        // Current flows: 12V → Relay COM → Relay NC → Pump → Ground
        // Pump starts running
    } else {
        digitalWrite(RELAY_PIN, LOW);   // Open relay circuit
        // Current flow stops
        // Pump stops running
    }
}
```

### Sensor Data Processing
```cpp
void processSensorData() {
    // Read soil moisture
    int moisture = readSoilMoisture();
    
    // Read temperature/humidity (if DHT11 connected)
    float temperature = readTemperature();
    float humidity = readHumidity();
    
    // Create status report
    DynamicJsonDocument status(256);
    status["device_id"] = "esp32_001";
    status["moisture"] = moisture;
    status["temperature"] = temperature;
    status["humidity"] = humidity;
    status["pump_status"] = digitalRead(RELAY_PIN) ? "ON" : "OFF";
    status["timestamp"] = getTimestamp();
    
    // Send to server
    publishStatus(status);
}
```

### Safety Features
```cpp
void checkSafetyConditions() {
    // Auto-stop if moisture is too high
    int moisture = readSoilMoisture();
    if (moisture > 80 && digitalRead(RELAY_PIN) == HIGH) {
        stopPump();
        Serial.println("⚠️ Auto-stop: Soil moisture too high");
    }
    
    // Check for pump runtime timeout
    static unsigned long pumpStartTime = 0;
    if (digitalRead(RELAY_PIN) == HIGH) {
        if (pumpStartTime == 0) pumpStartTime = millis();
        
        // Auto-stop after 10 minutes (600000ms)
        if (millis() - pumpStartTime > 600000) {
            stopPump();
            Serial.println("⚠️ Auto-stop: Pump runtime timeout");
        }
    } else {
        pumpStartTime = 0;
    }
}
```

## 📊 Real-time Data Flow

### Sensor → Server Communication
```cpp
void publishStatus(JsonDocument& status) {
    String topic = "agrosense/irrigation/esp32_001/status";
    String message;
    serializeJson(status, message);
    
    // Send to MQTT broker
    client.publish(topic, message.c_str());
    
    // Also send via HTTP as backup
    sendHTTPUpdate(status);
}
```

### Server → Dashboard Updates
```python
def mqtt_callback(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        device_id = msg.topic.split('/')[2]
        
        # Update cache with latest data
        cache_key = f"irrigation_status_{device_id}"
        cache.set(cache_key, data, 300)  # 5 minutes
        
        # Broadcast to connected web clients via WebSocket
        broadcast_to_clients(data)
        
    except Exception as e:
        print(f"Error processing MQTT message: {e}")
```

## 🛡️ Safety & Protection Features

### Electrical Safety
```cpp
void setupSafetyFeatures() {
    // Enable watchdog timer
    esp_task_wdt_init(5, true);
    esp_task_wdt_add(NULL);
    
    // Configure relay with safety defaults
    digitalWrite(RELAY_PIN, LOW);  // Start with pump OFF
    
    // Set up emergency stop pin (if needed)
    pinMode(EMERGENCY_STOP_PIN, INPUT_PULLUP);
}
```

### Software Safety
```cpp
void emergencyStop() {
    // Immediate pump shutdown
    digitalWrite(RELAY_PIN, LOW);
    digitalWrite(PUMP_LED_PIN, LOW);
    
    // Send emergency alert
    DynamicJsonDocument alert(128);
    alert["alert"] = "emergency_stop";
    alert["reason"] = "Manual emergency stop activated";
    alert["timestamp"] = getTimestamp();
    
    String topic = "agrosense/irrigation/esp32_001/alert";
    String message;
    serializeJson(alert, message);
    client.publish(topic, message.c_str());
}
```

## 🚀 Installation & Testing

### Step 1: Hardware Assembly
1. Connect all components according to wiring diagram
2. Double-check connections before applying power
3. Use breadboard for initial testing
4. Verify power supply voltage (12V DC)

### Step 2: Software Setup
1. Install Arduino IDE with ESP32 support
2. Install required libraries (WiFi, MQTT, ArduinoJson)
3. Upload firmware to ESP32
4. Test basic functionality

### Step 3: System Integration
1. Connect ESP32 to WiFi network
2. Test MQTT broker connection
3. Verify Django backend communication
4. Test complete control loop

### Step 4: Field Deployment
1. Install water pump in irrigation system
2. Place soil moisture sensor in representative location
3. Protect electronics from weather
4. Monitor initial operation

## 💰 Total Cost Breakdown

| Component | Cost (USD) | Quantity | Total |
|-----------|------------|----------|-------|
| ESP32 Board | $8-12 | 1 | $8-12 |
| Soil Moisture Sensor | $3-5 | 1 | $3-5 |
| Relay Module | $2-3 | 1 | $2-3 |
| Water Pump | $5-8 | 1 | $5-8 |
| Power Supply | $5-7 | 1 | $5-7 |
| Wiring/Connectors | $3-5 | - | $3-5 |
| **Total Cost** | | | **$26-40** |

This complete Smart Irrigation system provides professional-grade hardware control with real-time monitoring, safety features, and remote control capabilities. The system is designed for reliability, ease of installation, and scalability for agricultural applications.
