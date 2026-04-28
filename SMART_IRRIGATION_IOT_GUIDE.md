# Smart Irrigation IoT Hardware Guide

## Required IoT Components

### 1. Microcontroller
**ESP32 Development Board** (Recommended: ESP32-DevKitC or ESP32-WROOM-32)
- **Why ESP32:** Built-in WiFi/Bluetooth, dual-core processor, low power consumption
- **Power:** 3.3V logic, 5V tolerant inputs
- **Connectivity:** WiFi 802.11 b/g/n, Bluetooth v4.2 BR/EDR and BLE
- **GPIO:** 36 GPIO pins with multiple interfaces

### 2. Soil Moisture Sensor
**Capacitive Soil Moisture Sensor** (Recommended: V1.2 Capacitive Sensor)
- **Model:** Capacitive Soil Moisture Sensor V1.2
- **Voltage:** 3.3V - 5V DC
- **Output:** Analog voltage (0-3.3V)
- **Measurement Range:** 0-100% soil moisture
- **Advantages:** No corrosion, longer lifespan than resistive sensors

### 3. Relay Module
**5V Single Channel Relay Module** (Recommended: SRD-05VDC-SL-C)
- **Model:** Single Channel 5V Relay Module
- **Voltage:** 5V DC trigger voltage
- **Load Capacity:** 250V AC 10A / 30V DC 10A
- **Input:** 3.3V-5V compatible
- **Isolation:** Opto-isolated for safety

### 4. Water Pump
**12V DC Submersible Water Pump** (Recommended: 3-5L/min flow rate)
- **Model:** Mini DC 12V Water Pump
- **Voltage:** 12V DC
- **Flow Rate:** 3-5 liters per minute
- **Power:** 3-5W
- **Connection:** Standard hose fittings

### 5. Power Supply
**12V 2A DC Power Adapter**
- **Input:** 100-240V AC
- **Output:** 12V DC 2A
- **Connector:** 5.5mm barrel jack
- **Purpose:** Power water pump and relay

### 6. Optional Components
- **DHT11 Temperature/Humidity Sensor** (for environmental monitoring)
- **Water Flow Sensor** (to measure water usage)
- **Level Sensor** (for water tank monitoring)
- **Solar Panel + Battery** (for remote/off-grid deployment)

## Wiring Diagram & Pin Connections

### ESP32 Pin Connections

```
ESP32 Board Layout:
┌─────────────────────────────────────┐
│  EN  36  39  34  35  32  33  25  26  │
│  27  14  12  GND 13  SD2  SD3  CMD  │
│  5V  3V3  GND  TX0  RX0  D21  D19  D18│
│  D5   D6   D7   D8   D9   D10  D11  D12│
│  GND  VIN  3V3  GND  D13  SHD/SHD  SWP│
└─────────────────────────────────────┘
```

### Connection Details:

**1. Soil Moisture Sensor → ESP32**
```
Soil Moisture Sensor    →    ESP32
VCC (3.3V-5V)          →    3V3 (Pin 1)
GND                    →    GND (Pin 3)
AO (Analog Output)     →    GPIO34 (Pin 4) - ADC1_CH6
```

**2. Relay Module → ESP32**
```
Relay Module           →    ESP32
VCC                    →    5V (Pin 2)
GND                    →    GND (Pin 3)
IN (Signal)            →    GPIO26 (Pin 8)
```

**3. Water Pump → Relay**
```
Water Pump             →    Relay
+12V (Red)             →    Relay COM (Common)
Ground (Black)         →    Relay NC (Normally Closed)
```

**4. Power Supply Connections**
```
12V Power Adapter      →    System
+12V Output            →    Relay COM + Pump +
Ground                 →    Relay NC + Pump -
```

### Complete Wiring Diagram:

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

## Power Requirements

### Component Power Consumption:
- **ESP32:** ~240mA (WiFi active) / ~80mA (deep sleep)
- **Soil Moisture Sensor:** ~35mA
- **Relay Module:** ~70mA (when active)
- **Water Pump:** ~300-500mA (12V)

### Total Power Requirements:
- **Operating:** ~645-845mA @ 12V
- **Standby:** ~155mA @ 12V (pump off)
- **Deep Sleep:** ~80mA @ 12V (ESP32 sleep)

### Recommended Power Supply:
- **12V 2A DC Adapter** (provides 200% headroom)
- **Optional:** 12V 5A for multiple pumps or accessories

## Arduino/ESP32 Code Structure

### Required Libraries:
```cpp
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <PubSubClient.h> // For MQTT
```

### Pin Definitions:
```cpp
// ESP32 Pin Definitions
#define SOIL_MOISTURE_PIN 34    // ADC1_CH6
#define RELAY_PIN 26           // GPIO26
#define PUMP_LED_PIN 2         // Built-in LED

// Sensor calibration values
#define DRY_VALUE 2800         // ADC value for dry soil
#define WET_VALUE 1200         // ADC value for wet soil
```

### Basic Setup Code:
```cpp
void setup() {
  Serial.begin(115200);
  
  // Pin setup
  pinMode(RELAY_PIN, OUTPUT);
  pinMode(PUMP_LED_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);
  digitalWrite(PUMP_LED_PIN, LOW);
  
  // WiFi connection
  WiFi.begin("YOUR_SSID", "YOUR_PASSWORD");
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  
  Serial.println("WiFi connected!");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}
```

### Sensor Reading Function:
```cpp
int readSoilMoisture() {
  int rawValue = analogRead(SOIL_MOISTURE_PIN);
  
  // Convert ADC value to percentage (0-100%)
  int moisturePercent = map(rawValue, DRY_VALUE, WET_VALUE, 0, 100);
  moisturePercent = constrain(moisturePercent, 0, 100);
  
  return moisturePercent;
}
```

### Pump Control Functions:
```cpp
void startPump() {
  digitalWrite(RELAY_PIN, HIGH);
  digitalWrite(PUMP_LED_PIN, HIGH);
  Serial.println("Pump started");
}

void stopPump() {
  digitalWrite(RELAY_PIN, LOW);
  digitalWrite(PUMP_LED_PIN, LOW);
  Serial.println("Pump stopped");
}
```

## Installation Steps

### 1. Hardware Assembly
1. Connect all components according to wiring diagram
2. Double-check all connections before power
3. Install water pump in irrigation system
4. Place soil moisture sensor in representative location

### 2. Software Setup
1. Install Arduino IDE with ESP32 board support
2. Install required libraries
3. Upload firmware to ESP32
4. Test all functions manually

### 3. System Integration
1. Connect to Django backend via WiFi
2. Test API endpoints
3. Verify real-time data transmission
4. Test remote pump control

### 4. Deployment
1. Install in field location
2. Protect electronics from weather
3. Ensure proper power supply
4. Monitor initial operation

## Safety Considerations

### Electrical Safety:
- Use proper insulation for all connections
- Keep electronics away from water sources
- Use GFCI protection for outdoor installations
- Ensure proper grounding

### Water Safety:
- Use food-grade tubing for potable water
- Install check valves to prevent backflow
- Ensure proper drainage to prevent flooding
- Regular maintenance of pump and connections

### System Safety:
- Implement timeout protection for pump operation
- Add manual override switches
- Monitor for system faults
- Backup power options for critical applications

## Troubleshooting

### Common Issues:
1. **Sensor Reading 0%:** Check power and connections
2. **Pump Not Working:** Verify relay and power supply
3. **WiFi Connection Issues:** Check signal strength and credentials
4. **API Communication:** Verify server connectivity

### Debug Tools:
- Serial monitor for real-time debugging
- Multimeter for voltage testing
- Network analyzer for WiFi issues
- Logic analyzer for signal debugging

## Cost Breakdown (Approximate)

| Component | Cost (USD) | Quantity | Total |
|-----------|------------|----------|-------|
| ESP32 Board | $8-12 | 1 | $8-12 |
| Soil Moisture Sensor | $3-5 | 1 | $3-5 |
| Relay Module | $2-3 | 1 | $2-3 |
| Water Pump | $5-8 | 1 | $5-8 |
| Power Supply | $5-7 | 1 | $5-7 |
| Wiring/Connectors | $3-5 | - | $3-5 |
| **Total Cost** | | | **$26-40** |

This complete IoT setup provides a robust, scalable smart irrigation system that integrates seamlessly with the AgroSense Django backend.
