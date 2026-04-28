# Smart IoT-Based Irrigation + Controlled Environment Growth Chamber

## 🧠 SYSTEM ARCHITECTURE

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web/Mobile   │    │   Django       │    │   MQTT Broker  │    │   ESP32        │
│   Dashboard     │◄──►│   Backend      │◄──►│   (Mosquitto)  │◄──►│   Controller    │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │                       │
         ▼                       ▼                       ▼                       ▼
   User Interface         Database & APIs        Message Routing        Sensors & Actuators
```

## 📋 COMPLETE HARDWARE SPECIFICATIONS

### Controller Board
- **ESP32-WROOM-32** - Main controller
- **WiFi 802.11 b/g/n** - Network connectivity
- **Bluetooth 5.0** - Local configuration
- **GPIO 36 pins** - Device control
- **ADC 2 channels** - Sensor reading
- **3.3V logic** - Signal control

### Sensors Required
1. **Capacitive Soil Moisture Sensor V1.2**
   - Voltage: 3.3V-5V DC
   - Output: Analog 0-3.3V
   - Range: 0-100% moisture
   - Cost: $3-5

2. **DHT22 Temperature & Humidity Sensor**
   - Temperature: -40 to 80°C (±0.5°C)
   - Humidity: 0-100% RH (±2%)
   - Digital output (single-wire)
   - Cost: $4-6

3. **LDR Light Sensor (Optional)**
   - Photoresistor with voltage divider
   - Analog output 0-3.3V
   - Cost: $1-2

### Actuators Required
1. **12V DC Water Pump** (3-5L/min)
   - Power: 12V DC, 3-5W
   - Flow rate: 3-5 liters/minute
   - Cost: $5-8

2. **12V DC Cooling Fan**
   - Voltage: 12V DC
   - Current: 0.3A
   - Airflow: 40 CFM
   - Cost: $3-5

3. **5V LED Grow Light**
   - Power: 5V DC, 10W
   - Spectrum: Full spectrum (400-700nm)
   - Cost: $8-12

4. **5V Ultrasonic Humidifier**
   - Voltage: 5V DC
   - Mist output: 20ml/hour
   - Cost: $6-8

5. **12V Heating Element (Optional)**
   - Voltage: 12V DC
   - Power: 20W
   - Temperature control: 0-40°C
   - Cost: $10-15

### Power Management
- **12V 5A Power Supply** - Main power
- **5V 3A Buck Converter** - LED logic
- **3.3V LDO Regulator** - ESP32 power
- **Fuse Protection** - 5A automotive fuse
- **Total Cost**: $45-70

## 🔌 COMPLETE WIRING DIAGRAM

### Power Distribution
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            12V 5A POWER SUPPLY                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│  +12V ────┬─────────────────────────────────────────────────────────────┐   │
│            │                                                         │   │
│            ├─[5A FUSE]─┬─────────────────────────────────────────────┐   │   │
│            │            │                                     │   │   │   │
│            │            ├─[12V PUMP]────────────────────────────┐   │   │   │
│            │            │                                     │   │   │   │
│            │            ├─[12V FAN]────────────────────────────┐   │   │   │
│            │            │                                     │   │   │   │
│            │            └─[12V HEATER] (optional)───────────────┐   │   │   │
│            │                                                  │   │   │   │
│  GND ──────┴──────────────────────────────────────────────────────┴───┴───┴───┘   │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                        5V 3A BUCK CONVERTER                        │
├─────────────────────────────────────────────────────────────────────────────────┤
│  INPUT: 12V DC                                                    │
│  OUTPUT: 5V DC                                                     │
│                                                                     │
│  +5V ────┬─────────────────────────────────────────────────────────────┐   │
│           │                                                         │   │
│           ├─[LED GROW LIGHT]───────────────────────────────────────┐   │   │
│           │                                                     │   │   │
│           └─[ULTRASONIC HUMIDIFIER]─────────────────────────────┐   │   │
│                                                                 │   │   │
│  GND ─────────────────────────────────────────────────────────────┴───┴───┘   │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                      3.3V LDO REGULATOR                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│  INPUT: 5V DC                                                      │
│  OUTPUT: 3.3V DC                                                    │
│                                                                     │
│  +3.3V ────┬───────────────────────────────────────────────────────────┐   │
│             │                                                       │   │
│             ├─[ESP32 3.3V]                                        │   │   │
│             ├─[DHT22 VCC]                                          │   │   │
│             ├─[SOIL MOISTURE VCC]                                   │   │   │
│             └─[LDR VCC] (optional)                                  │   │   │
│                                                                     │   │
│  GND ────────┬───────────────────────────────────────────────────────────┴───┘   │
│              │                                                             │
│              ├─[ESP32 GND]                                                │
│              ├─[DHT22 GND]                                                │
│              ├─[SOIL MOISTURE GND]                                         │
│              └─[LDR GND] (optional)                                       │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Signal Control (Low Voltage)
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           ESP32 GPIO CONTROL                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ GPIO26 ────┬─────────────────────────────────────────────────────────────┐   │
│            │                                                         │   │
│            ├─[1K RESISTOR]─[OPTOCOUPLER LED]─[GND]               │   │   │
│            │                                                         │   │   │
│            └─[RELAY COIL]─[FLYBACK DIODE]─[+12V]                │   │   │
│                                                                     │   │
│ GPIO27 ────┬─────────────────────────────────────────────────────────────┐   │
│            │                                                         │   │
│            ├─[1K RESISTOR]─[MOSFET GATE]                           │   │   │
│            │                                                         │   │   │
│            └─[FAN DRAIN]─[FLYBACK DIODE]─[+12V]                  │   │   │
│                                                                     │   │
│ GPIO25 ────┬─────────────────────────────────────────────────────────────┐   │
│            │                                                         │   │
│            ├─[1K RESISTOR]─[MOSFET GATE]                           │   │   │
│            │                                                         │   │   │
│            └─[HEATER DRAIN]─[FLYBACK DIODE]─[+12V]                │   │   │
│                                                                     │   │
│ GPIO33 ────┬─────────────────────────────────────────────────────────────┐   │
│            │                                                         │   │
│            ├─[220Ω RESISTOR]─[LED ANODE]                            │   │   │
│            │                                                         │   │   │
│            └─[LED CATHODE]─[GND]                                    │   │   │
│                                                                     │   │
│ GPIO4 ──────┬─────────────────────────────────────────────────────────────┐   │
│             │                                                         │   │
│             ├─[1K RESISTOR]─[MOSFET GATE]                           │   │   │
│             │                                                         │   │   │
│             └─[HUMIDIFIER DRAIN]─[FLYBACK DIODE]─[+5V]             │   │   │
│                                                                     │   │
│ GPIO34 ──────[SOIL MOISTURE AO]                                        │
│ GPIO32 ──────[DHT22 DATA]                                             │
│ GPIO35 ──────[LDR AO] (optional)                                       │
│                                                                     │
│ GND ──────────────────────────────────────────────────────────────────────────┘
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 📡 MQTT TOPIC STRUCTURE

### Command Topics (User → ESP32)
```
agrosense/chamber/{device_id}/command/
├── irrigation/
│   ├── pump
│   ├── schedule
│   └── mode
├── environment/
│   ├── temperature
│   ├── humidity
│   ├── light
│   └── fan
└── system/
    ├── emergency_stop
    ├── reboot
    └── calibration
```

### Data Topics (ESP32 → Server)
```
agrosense/chamber/{device_id}/data/
├── sensors/
│   ├── temperature
│   ├── humidity
│   ├── moisture
│   └── light
├── status/
│   ├── pump
│   ├── fan
│   ├── heater
│   ├── light
│   └── humidifier
└── system/
    ├── uptime
    ├── wifi_signal
    └── errors
```

### Message Format (JSON)
```json
{
  "timestamp": "2024-04-28T19:30:00Z",
  "device_id": "chamber_001",
  "command": "set_pump",
  "value": true,
  "duration": 300,
  "source": "web_dashboard"
}
```

## 🔐 SECURITY IMPLEMENTATION

### MQTT Authentication
```python
# Mosquitto Configuration
allow_anonymous false
password_file /etc/mosquitto/passwd
acl_file /etc/mosquitto/acl

# User Authentication
username: agrosense_user
password: secure_hashed_password
```

### Topic ACL (Access Control)
```
# User agrosense_user can publish/subscribe to all topics
user agrosense_user
topic readwrite agrosense/chamber/#

# Guest users can only read sensor data
user guest
topic read agrosense/chamber/+/data/sensors/#
```

### Django Security
```python
# API Authentication
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# MQTT Security
MQTT_BROKER_CONFIG = {
    'HOST': 'mqtt.agrosense.com',
    'PORT': 8883,
    'USERNAME': 'agrosense_user',
    'PASSWORD': os.environ.get('MQTT_PASSWORD'),
    'USE_SSL': True,
    'CA_CERT': '/path/to/ca.crt',
}
```

## 🧪 TESTING PROCEDURES

### Phase 1: Hardware Testing
1. **Power Supply Test**
   - Verify 12V, 5V, 3.3V outputs
   - Check current draw under load
   - Test fuse protection

2. **Sensor Calibration**
   - Soil moisture: dry (0%) and wet (100%) points
   - DHT22: compare with reference thermometer
   - LDR: dark/light conditions

3. **Actuator Testing**
   - Pump activation/deactivation
   - Fan speed control
   - LED brightness
   - Humidifier mist output

### Phase 2: Communication Testing
1. **WiFi Connection**
   - Signal strength at different locations
   - Reconnection after power loss
   - Network stability

2. **MQTT Communication**
   - Command reception
   - Data publishing
   - Message delivery confirmation

### Phase 3: Integration Testing
1. **End-to-End Control**
   - Web dashboard → MQTT → ESP32 → Hardware
   - Sensor data → ESP32 → MQTT → Dashboard
   - Real-time updates verification

2. **Failure Scenarios**
   - Network disconnection
   - Power outage recovery
   - Sensor failure handling

## 📦 COMPONENT COST BREAKDOWN

| Component | Quantity | Unit Cost | Total | Notes |
|------------|-----------|------------|---------|-------|
| ESP32-WROOM-32 | 1 | $8 | $8 | Main controller |
| Soil Moisture Sensor | 1 | $4 | $4 | Capacitive V1.2 |
| DHT22 Sensor | 1 | $5 | $5 | Temp/Humidity |
| LDR Sensor | 1 | $1 | $1 | Optional light |
| 12V Water Pump | 1 | $6 | $6 | 3-5L/min |
| 12V Cooling Fan | 1 | $4 | $4 | 40 CFM |
| 5V LED Grow Light | 1 | $10 | $10 | Full spectrum |
| 5V Humidifier | 1 | $7 | $7 | Ultrasonic |
| 12V Heater | 1 | $12 | $12 | Optional |
| 12V 5A Power Supply | 1 | $15 | $15 | Main power |
| 5V 3A Buck Converter | 1 | $5 | $5 | Voltage regulation |
| 3.3V LDO Regulator | 1 | $2 | $2 | ESP32 power |
| Relay Module | 1 | $3 | $3 | Pump control |
| MOSFETs (IRLZ44N) | 3 | $1 | $3 | Fan/Heater/Humidifier |
| Optocouplers (PC817) | 2 | $0.5 | $1 | Isolation |
| Diodes (1N4007) | 4 | $0.2 | $0.8 | Flyback protection |
| Resistors (assorted) | 20 | $0.1 | $2 | Signal conditioning |
| PCB/Protoboard | 1 | $5 | $5 | Assembly |
| Wiring/Connectors | 1 | $8 | $8 | Connections |
| **TOTAL** | | | **$88.80** | |

This system provides professional-grade IoT control for both irrigation and environment management with comprehensive safety features and reliable operation.
