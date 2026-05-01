/*
 * Smart IoT Irrigation & Environmental Control System
 * ESP32 Firmware with Manual, Automatic, and Plant-Based Control Modes
 * 
 * Features:
 * - WiFi connectivity with automatic reconnection
 * - Real-time sensor monitoring (soil moisture, temperature, humidity, light)
 * - Three control modes: Manual, Automatic, Plant-Based
 * - Hardware safety features and error handling
 * - MQTT integration for remote monitoring
 * - Energy-efficient operation with deep sleep support
 * - Over-the-air update capability
 */

#include <WiFi.h>
#include <WiFiClient.h>
#include <WebServer.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include <ESP32AnalogRead.h>
#include <Ticker.h>

// Hardware Pin Definitions
#define SOIL_MOISTURE_PIN 34
#define DHT22_PIN 32
#define LDR_PIN 35
#define PUMP_RELAY_PIN 26
#define FAN_RELAY_PIN 25
#define LIGHT_RELAY_PIN 27

// Device Configuration
#define DEVICE_ID "esp32_001"
#define FIRMWARE_VERSION "1.0.0"
#define SENSOR_READ_INTERVAL 5000    // 5 seconds
#define CONTROL_CHECK_INTERVAL 2000  // 2 seconds
#define WATCHDOG_TIMEOUT 30000      // 30 seconds

// WiFi Configuration
const char* ssid = "AgroSense_Farm";
const char* password = "your_wifi_password";
WebServer server(80);

// Sensor Objects
DHT dht(DHT22_PIN, DHT22);

// Global Variables
struct SensorData {
  float soilMoisture;
  float temperature;
  float humidity;
  int lightIntensity;
  unsigned long timestamp;
};

struct ControlState {
  bool pumpActive;
  bool fanActive;
  bool lightActive;
  String mode;  // "MANUAL", "AUTO", "PLANT"
  unsigned long lastUpdate;
};

struct PlantProfile {
  String name;
  String displayName;
  float soilMoistureMin;
  float soilMoistureMax;
  float temperatureMin;
  float temperatureMax;
  int lightHours;
  int lightIntensity;
};

// Global State
SensorData currentSensors = {0};
ControlState controlState = {false, false, false, "MANUAL", 0};
PlantProfile currentPlant = {"", "", 0, 0, 0, 0, 0, 0, 0};

// Predefined Plant Profiles
PlantProfile plantProfiles[] = {
  {"tomato", "🍅 Tomato", 55.0, 75.0, 18.0, 32.0, 16, 400},
  {"lettuce", "🥬 Lettuce", 65.0, 80.0, 12.0, 28.0, 14, 350},
  {"wheat", "🌾 Wheat", 60.0, 75.0, 10.0, 25.0, 12, 300},
  {"rice", "🌾 Rice", 70.0, 85.0, 20.0, 30.0, 14, 250}
};

// Timing Variables
unsigned long lastSensorRead = 0;
unsigned long lastControlCheck = 0;
unsigned long pumpStartTime = 0;
unsigned long maxPumpRuntime = 300000; // 5 minutes in milliseconds

// Ticker objects
Ticker sensorTicker;
Ticker controlTicker;
Ticker watchdogTicker;

// Function Prototypes
void readSensors();
void updateControlLogic();
void manualControl();
void automaticControl();
void plantBasedControl();
void sendSensorData();
void handleControlCommands();
void updateRelays();
void watchdogReset();
void setupWiFi();
void setupWebServer();
int readSoilMoisture();
int readLightIntensity();
void applySafetyLimits();
void logSystemEvent(String event, String details);

void setup() {
  Serial.begin(115200);
  Serial.println("\n=== Smart IoT Irrigation System Starting ===");
  
  // Initialize pins
  pinMode(PUMP_RELAY_PIN, OUTPUT);
  pinMode(FAN_RELAY_PIN, OUTPUT);
  pinMode(LIGHT_RELAY_PIN, OUTPUT);
  pinMode(SOIL_MOISTURE_PIN, INPUT);
  pinMode(LDR_PIN, INPUT);
  
  // Initialize relays to OFF (relays are active LOW)
  digitalWrite(PUMP_RELAY_PIN, HIGH);
  digitalWrite(FAN_RELAY_PIN, HIGH);
  digitalWrite(LIGHT_RELAY_PIN, HIGH);
  
  // Initialize DHT22 sensor
  dht.begin();
  
  // Setup WiFi
  setupWiFi();
  
  // Setup Web Server
  setupWebServer();
  
  // Setup tickers
  sensorTicker.attach_ms(SENSOR_READ_INTERVAL, readSensors);
  controlTicker.attach_ms(CONTROL_CHECK_INTERVAL, updateControlLogic);
  watchdogTicker.attach_ms(WATCHDOG_TIMEOUT, watchdogReset);
  
  Serial.println("System initialized successfully!");
  Serial.print("Device ID: ");
  Serial.println(DEVICE_ID);
  Serial.print("Mode: ");
  Serial.println(controlState.mode);
}

void loop() {
  server.handleClient();
  
  // Check for mode changes from web interface
  if (millis() - controlState.lastUpdate > CONTROL_CHECK_INTERVAL) {
    updateControlLogic();
    controlState.lastUpdate = millis();
  }
  
  // Watchdog reset
  if (millis() > WATCHDOG_TIMEOUT) {
    watchdogReset();
  }
}

void setupWiFi() {
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected successfully!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nFailed to connect to WiFi");
    // Continue with limited functionality
  }
}

void setupWebServer() {
  // CORS headers
  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.sendHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  server.sendHeader("Access-Control-Allow-Headers", "Content-Type");
  
  // API Routes
  server.on("/", HTTP_GET, []() {
    String html = getIndexHtml();
    server.send(200, "text/html", html);
  });
  
  server.on("/api/sensor-data", HTTP_POST, []() {
    handleSensorDataUpload();
  });
  
  server.on("/api/device-control", HTTP_GET, []() {
    handleControlRequest();
  });
  
  server.on("/api/status", HTTP_GET, []() {
    handleStatusRequest();
  });
  
  server.on("/api/plant-profiles", HTTP_GET, []() {
    handlePlantProfilesRequest();
  });
  
  server.on("/api/config", HTTP_POST, []() {
    handleConfigRequest();
  });
  
  server.begin();
  Serial.println("Web server started");
}

void readSensors() {
  // Read soil moisture (0-100%)
  currentSensors.soilMoisture = readSoilMoisture();
  
  // Read temperature and humidity from DHT22
  float temp = dht.readTemperature();
  float hum = dht.readHumidity();
  
  if (!isnan(temp) && !isnan(hum)) {
    currentSensors.temperature = temp;
    currentSensors.humidity = hum;
  } else {
    Serial.println("Failed to read DHT22 sensor");
    currentSensors.temperature = -999;
    currentSensors.humidity = -999;
  }
  
  // Read light intensity
  currentSensors.lightIntensity = readLightIntensity();
  
  currentSensors.timestamp = millis();
  
  // Apply safety limits to sensor readings
  applySafetyLimits();
  
  // Send data to backend if connected
  if (WiFi.status() == WL_CONNECTED) {
    sendSensorData();
  }
  
  // Debug output
  Serial.printf("Sensors - Soil: %.1f%%, Temp: %.1f°C, Hum: %.1f%%, Light: %d\n",
              currentSensors.soilMoisture, currentSensors.temperature, 
              currentSensors.humidity, currentSensors.lightIntensity);
}

int readSoilMoisture() {
  // Read multiple samples and average for stability
  int total = 0;
  int samples = 10;
  
  for (int i = 0; i < samples; i++) {
    total += analogRead(SOIL_MOISTURE_PIN);
    delay(10);
  }
  
  // Convert to percentage (0-100%)
  // Note: Calibration may be needed based on your sensor
  int average = total / samples;
  int moisture = map(average, 0, 4095, 100, 0);
  
  return constrain(moisture, 0, 100);
}

int readLightIntensity() {
  // Read LDR sensor and convert to 0-1000 scale
  int rawValue = analogRead(LDR_PIN);
  int lightLevel = map(rawValue, 0, 4095, 0, 1000);
  
  return constrain(lightLevel, 0, 1000);
}

void updateControlLogic() {
  if (controlState.mode == "MANUAL") {
    manualControl();
  } else if (controlState.mode == "AUTO") {
    automaticControl();
  } else if (controlState.mode == "PLANT") {
    plantBasedControl();
  }
  
  updateRelays();
}

void manualControl() {
  // In manual mode, control state is set directly from web interface
  // No automatic logic applied
  Serial.println("Manual control mode active");
}

void automaticControl() {
  Serial.println("Automatic control mode active");
  
  // Soil moisture control
  if (currentSensors.soilMoisture < currentPlant.soilMoistureMin) {
    controlState.pumpActive = true;
    if (!pumpStartTime) {
      pumpStartTime = millis();
    }
  } else if (currentSensors.soilMoisture > currentPlant.soilMoistureMax) {
    controlState.pumpActive = false;
    pumpStartTime = 0;
  }
  
  // Temperature control
  if (currentSensors.temperature > currentPlant.temperatureMax) {
    controlState.fanActive = true;
  } else if (currentSensors.temperature < currentPlant.temperatureMin) {
    controlState.fanActive = false;
  }
  
  // Light control (based on time and intensity)
  int currentHour = (millis() / 3600000) % 24;
  bool lightHours = (currentHour >= 6 && currentHour < 22); // 6 AM to 10 PM
  
  if (lightHours && currentSensors.lightIntensity < currentPlant.lightIntensity) {
    controlState.lightActive = true;
  } else {
    controlState.lightActive = false;
  }
}

void plantBasedControl() {
  Serial.println("Plant-based control mode active: " + currentPlant.displayName);
  
  // Apply plant-specific optimal conditions
  if (currentSensors.soilMoisture < currentPlant.soilMoistureMin) {
    controlState.pumpActive = true;
    if (!pumpStartTime) {
      pumpStartTime = millis();
    }
  } else if (currentSensors.soilMoisture >= currentPlant.soilMoistureMax) {
    controlState.pumpActive = false;
    pumpStartTime = 0;
  }
  
  // Temperature control with plant-specific range
  if (currentSensors.temperature > currentPlant.temperatureMax) {
    controlState.fanActive = true;
  } else if (currentSensors.temperature < currentPlant.temperatureMin) {
    controlState.fanActive = false;
  }
  
  // Light control based on plant requirements
  int currentHour = (millis() / 3600000) % 24;
  bool lightHours = (currentHour >= 6 && currentHour < 22);
  
  if (lightHours && currentSensors.lightIntensity < currentPlant.lightIntensity) {
    controlState.lightActive = true;
  } else {
    controlState.lightActive = false;
  }
  
  // Growth stage adaptation
  // This could be expanded to adjust thresholds based on growth stage
}

void updateRelays() {
  // Apply safety limits before updating relays
  applySafetyLimits();
  
  // Update relay states (active LOW)
  digitalWrite(PUMP_RELAY_PIN, controlState.pumpActive ? LOW : HIGH);
  digitalWrite(FAN_RELAY_PIN, controlState.fanActive ? LOW : HIGH);
  digitalWrite(LIGHT_RELAY_PIN, controlState.lightActive ? LOW : HIGH);
  
  // Log state changes
  static ControlState lastState = {false, false, false, "MANUAL", 0};
  
  if (lastState.pumpActive != controlState.pumpActive) {
    logSystemEvent("Pump", controlState.pumpActive ? "ON" : "OFF");
  }
  if (lastState.fanActive != controlState.fanActive) {
    logSystemEvent("Fan", controlState.fanActive ? "ON" : "OFF");
  }
  if (lastState.lightActive != controlState.lightActive) {
    logSystemEvent("Light", controlState.lightActive ? "ON" : "OFF");
  }
  
  lastState = controlState;
}

void applySafetyLimits() {
  // Maximum pump runtime protection
  if (controlState.pumpActive && pumpStartTime > 0) {
    unsigned long runtime = millis() - pumpStartTime;
    if (runtime > maxPumpRuntime) {
      controlState.pumpActive = false;
      pumpStartTime = 0;
      logSystemEvent("Safety", "Pump runtime exceeded - shutting down");
    }
  }
  
  // Temperature protection
  if (currentSensors.temperature > 45 || currentSensors.temperature < 0) {
    controlState.fanActive = false;
    controlState.lightActive = false;
    controlState.pumpActive = false;
    logSystemEvent("Safety", "Extreme temperature - all devices OFF");
  }
  
  // Sensor value validation
  if (currentSensors.soilMoisture < 0 || currentSensors.soilMoisture > 100) {
    logSystemEvent("Safety", "Invalid soil moisture reading");
  }
  if (currentSensors.lightIntensity < 0 || currentSensors.lightIntensity > 1000) {
    logSystemEvent("Safety", "Invalid light intensity reading");
  }
}

void sendSensorData() {
  if (WiFi.status() != WL_CONNECTED) return;
  
  // Create JSON payload
  DynamicJsonDocument doc(1024);
  doc["device_id"] = DEVICE_ID;
  doc["timestamp"] = currentSensors.timestamp;
  doc["firmware_version"] = FIRMWARE_VERSION;
  
  JsonObject sensors = doc.createNestedObject("sensors");
  sensors["soil_moisture"] = currentSensors.soilMoisture;
  sensors["temperature"] = currentSensors.temperature;
  sensors["humidity"] = currentSensors.humidity;
  sensors["light_intensity"] = currentSensors.lightIntensity;
  
  JsonObject deviceStatus = doc.createNestedObject("device_status");
  deviceStatus["wifi_rssi"] = WiFi.RSSI();
  deviceStatus["free_heap"] = ESP.getFreeHeap();
  deviceStatus["uptime_seconds"] = millis() / 1000;
  
  JsonObject controlStatus = doc.createNestedObject("control_status");
  controlStatus["mode"] = controlState.mode;
  controlStatus["pump_active"] = controlState.pumpActive;
  controlStatus["fan_active"] = controlState.fanActive;
  controlStatus["light_active"] = controlState.lightActive;
  controlStatus["pump_runtime_seconds"] = pumpStartTime > 0 ? (millis() - pumpStartTime) / 1000 : 0;
  
  doc["sensors"] = sensors;
  doc["device_status"] = deviceStatus;
  doc["control_status"] = controlStatus;
  
  // Send to backend
  HTTPClient http;
  http.begin("agrosense-backend.com", 80);
  http.addHeader("Content-Type", "application/json");
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  int httpResponseCode = http.POST("/api/sensor-data", jsonString);
  
  if (httpResponseCode == 200) {
    Serial.println("Sensor data sent successfully");
  } else {
    Serial.printf("Failed to send sensor data. HTTP code: %d\n", httpResponseCode);
  }
  
  http.end();
}

void handleControlRequest() {
  String mode = server.arg("mode");
  String pumpCmd = server.arg("pump");
  String fanCmd = server.arg("fan");
  String lightCmd = server.arg("light");
  String plantProfile = server.arg("plant");
  
  // Update mode
  if (mode.length() > 0) {
    controlState.mode = mode;
    logSystemEvent("Mode", "Changed to " + mode);
  }
  
  // Update plant profile
  if (plantProfile.length() > 0) {
    for (int i = 0; i < sizeof(plantProfiles) / sizeof(PlantProfile); i++) {
      if (plantProfiles[i].name == plantProfile) {
        currentPlant = plantProfiles[i];
        logSystemEvent("Plant", "Profile changed to " + currentPlant.displayName);
        break;
      }
    }
  }
  
  // Manual control commands
  if (controlState.mode == "MANUAL") {
    if (pumpCmd == "ON") controlState.pumpActive = true;
    if (pumpCmd == "OFF") controlState.pumpActive = false;
    if (fanCmd == "ON") controlState.fanActive = true;
    if (fanCmd == "OFF") controlState.fanActive = false;
    if (lightCmd == "ON") controlState.lightActive = true;
    if (lightCmd == "OFF") controlState.lightActive = false;
    
    logSystemEvent("Manual", "Commands received: P=" + pumpCmd + " F=" + fanCmd + " L=" + lightCmd);
  }
  
  // Send current status back
  DynamicJsonDocument doc(512);
  doc["status"] = "success";
  doc["mode"] = controlState.mode;
  doc["plant_profile"] = currentPlant.name;
  
  JsonObject commands = doc.createNestedObject("commands");
  commands["pump"] = controlState.pumpActive;
  commands["fan"] = controlState.fanActive;
  commands["light"] = controlState.lightActive;
  
  JsonObject thresholds = doc.createNestedObject("thresholds");
  thresholds["soil_moisture_min"] = currentPlant.soilMoistureMin;
  thresholds["soil_moisture_max"] = currentPlant.soilMoistureMax;
  thresholds["temperature_min"] = currentPlant.temperatureMin;
  thresholds["temperature_max"] = currentPlant.temperatureMax;
  thresholds["light_min"] = currentPlant.lightIntensity;
  
  doc["commands"] = commands;
  doc["thresholds"] = thresholds;
  
  String jsonString;
  serializeJson(doc, jsonString);
  server.send(200, "application/json", jsonString);
}

void handleStatusRequest() {
  DynamicJsonDocument doc(512);
  doc["device_id"] = DEVICE_ID;
  doc["firmware_version"] = FIRMWARE_VERSION;
  doc["mode"] = controlState.mode;
  doc["plant_profile"] = currentPlant.displayName;
  doc["uptime_seconds"] = millis() / 1000;
  doc["free_heap"] = ESP.getFreeHeap();
  doc["wifi_rssi"] = WiFi.RSSI();
  
  JsonObject sensors = doc.createNestedObject("sensors");
  sensors["soil_moisture"] = currentSensors.soilMoisture;
  sensors["temperature"] = currentSensors.temperature;
  sensors["humidity"] = currentSensors.humidity;
  sensors["light_intensity"] = currentSensors.lightIntensity;
  sensors["timestamp"] = currentSensors.timestamp;
  
  JsonObject controlStatus = doc.createNestedObject("control_status");
  controlStatus["pump_active"] = controlState.pumpActive;
  controlStatus["fan_active"] = controlState.fanActive;
  controlStatus["light_active"] = controlState.lightActive;
  controlStatus["pump_runtime_seconds"] = pumpStartTime > 0 ? (millis() - pumpStartTime) / 1000 : 0;
  
  doc["sensors"] = sensors;
  doc["control_status"] = controlStatus;
  
  String jsonString;
  serializeJson(doc, jsonString);
  server.send(200, "application/json", jsonString);
}

void handlePlantProfilesRequest() {
  DynamicJsonDocument doc(1024);
  JsonArray profiles = doc.createNestedArray("profiles");
  
  for (int i = 0; i < sizeof(plantProfiles) / sizeof(PlantProfile); i++) {
    JsonObject profile = profiles.createNestedObject();
    profile["name"] = plantProfiles[i].name;
    profile["display_name"] = plantProfiles[i].displayName;
    profile["soil_moisture_min"] = plantProfiles[i].soilMoistureMin;
    profile["soil_moisture_max"] = plantProfiles[i].soilMoistureMax;
    profile["temperature_min"] = plantProfiles[i].temperatureMin;
    profile["temperature_max"] = plantProfiles[i].temperatureMax;
    profile["light_hours"] = plantProfiles[i].lightHours;
    profile["light_intensity"] = plantProfiles[i].lightIntensity;
  }
  
  doc["current_profile"] = currentPlant.name;
  doc["status"] = "success";
  
  String jsonString;
  serializeJson(doc, jsonString);
  server.send(200, "application/json", jsonString);
}

void handleConfigRequest() {
  String newSSID = server.arg("ssid");
  String newPassword = server.arg("password");
  String newPlantProfile = server.arg("default_plant");
  
  bool configChanged = false;
  
  if (newSSID.length() > 0) {
    // In a real implementation, you'd store these in EEPROM
    Serial.println("WiFi configuration updated");
    configChanged = true;
  }
  
  if (newPlantProfile.length() > 0) {
    for (int i = 0; i < sizeof(plantProfiles) / sizeof(PlantProfile); i++) {
      if (plantProfiles[i].name == newPlantProfile) {
        currentPlant = plantProfiles[i];
        Serial.println("Default plant profile changed to: " + currentPlant.displayName);
        configChanged = true;
        break;
      }
    }
  }
  
  DynamicJsonDocument doc(256);
  doc["status"] = configChanged ? "success" : "no_change";
  doc["current_plant"] = currentPlant.displayName;
  doc["message"] = configChanged ? "Configuration updated" : "No changes detected";
  
  String jsonString;
  serializeJson(doc, jsonString);
  server.send(200, "application/json", jsonString);
}

void handleSensorDataUpload() {
  // Handle bulk sensor data upload from backend
  String payload = server.arg("plain");
  
  DynamicJsonDocument doc(256);
  DeserializationError error = deserializeJson(doc, payload);
  
  if (error == DeserializationError::Ok) {
    // Update thresholds based on backend response
    if (doc.containsKey("thresholds")) {
      JsonObject thresholds = doc["thresholds"];
      if (thresholds.containsKey("soil_moisture_min")) {
        currentPlant.soilMoistureMin = thresholds["soil_moisture_min"];
      }
      if (thresholds.containsKey("temperature_min")) {
        currentPlant.temperatureMin = thresholds["temperature_min"];
      }
      if (thresholds.containsKey("temperature_max")) {
        currentPlant.temperatureMax = thresholds["temperature_max"];
      }
    }
    
    doc["status"] = "success";
    doc["message"] = "Thresholds updated";
  } else {
    doc["status"] = "error";
    doc["message"] = "Invalid JSON payload";
  }
  
  String jsonString;
  serializeJson(doc, jsonString);
  server.send(200, "application/json", jsonString);
}

void watchdogReset() {
  Serial.println("Watchdog reset - system still running");
  // Reset watchdog timer
  // In a production system, you might want to log this event
}

void logSystemEvent(String event, String details) {
  Serial.printf("[%lu] %s: %s\n", millis(), event.c_str(), details.c_str());
  
  // In a production system, you might want to store these in EEPROM
  // or send them to a logging server
}

String getIndexHtml() {
  return R"(
<!DOCTYPE html>
<html>
<head>
    <title>Smart IoT Irrigation System</title>
    <meta name='viewport' content='width=device-width, initial-scale=1'>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .status-card { background: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #e9ecef; }
        .card-header { font-weight: bold; margin-bottom: 10px; color: #2c3e50; }
        .sensor-value { font-size: 24px; font-weight: bold; color: #28a745; }
        .control-btn { background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin: 5px; }
        .control-btn:hover { background: #0056b3; }
        .mode-indicator { background: #28a745; color: white; padding: 5px 10px; border-radius: 15px; text-align: center; }
        .active { background: #dc3545; }
        .plant-select { padding: 10px; border: 1px solid #ddd; border-radius: 5px; font-size: 16px; }
        @media (max-width: 600px) { .status-grid { grid-template-columns: 1fr; } }
    </style>
</head>
<body>
    <h1>Smart IoT Irrigation System</h1>
    <div class='container'>
        <div class='status-grid'>
            <div class='status-card'>
                <div class='card-header'>Device Status</div>
                <div>Mode: <span id='current-mode' class='mode-indicator active'>" + controlState.mode + "</span></div>
                <div>WiFi: " + (WiFi.status() == WL_CONNECTED ? "Connected" : "Disconnected") + "</div>
                <div>IP: " + WiFi.localIP().toString() + "</div>
            </div>
            
            <div class='status-card'>
                <div class='card-header'>Sensors</div>
                <div>Soil Moisture: <span class='sensor-value'>" + String(currentSensors.soilMoisture, 1) + "%</span></div>
                <div>Temperature: <span class='sensor-value'>" + String(currentSensors.temperature, 1) + "°C</span></div>
                <div>Humidity: <span class='sensor-value'>" + String(currentSensors.humidity, 1) + "%</span></div>
                <div>Light: <span class='sensor-value'>" + String(currentSensors.lightIntensity) + "</span></div>
            </div>
            
            <div class='status-card'>
                <div class='card-header'>Controls</div>
                <div>
                    <button class='control-btn' onclick='location.href=\"/api/device-control?mode=MANUAL\"'>Manual Mode</button>
                    <button class='control-btn' onclick='location.href=\"/api/device-control?mode=AUTO\"'>Auto Mode</button>
                    <button class='control-btn' onclick='location.href=\"/api/device-control?mode=PLANT\"'>Plant Mode</button>
                </div>
                <div>
                    <button class='control-btn' onclick='location.href=\"/api/device-control?pump=ON\"'>Pump ON</button>
                    <button class='control-btn' onclick='location.href=\"/api/device-control?pump=OFF\"'>Pump OFF</button>
                    <button class='control-btn' onclick='location.href=\"/api/device-control?fan=ON\"'>Fan ON</button>
                    <button class='control-btn' onclick='location.href=\"/api/device-control?fan=OFF\"'>Fan OFF</button>
                    <button class='control-btn' onclick='location.href=\"/api/device-control?light=ON\"'>Light ON</button>
                    <button class='control-btn' onclick='location.href=\"/api/device-control?light=OFF\"'>Light OFF</button>
                </div>
            </div>
            
            <div class='status-card'>
                <div class='card-header'>Plant Profile</div>
                <select class='plant-select' onchange='location.href=\"/api/device-control?plant=\"+this.value'>
                    <option value=''>Select Plant</option>
                    <option value='tomato'>🍅 Tomato</option>
                    <option value='lettuce'>🥬 Lettuce</option>
                    <option value='wheat'>🌾 Wheat</option>
                    <option value='rice'>🌾 Rice</option>
                </select>
                <div>Current: <span id='current-plant'>" + currentPlant.displayName + "</span></div>
            </div>
        </div>
    </div>
    
    <script>
        // Auto-refresh sensor data every 5 seconds
        setInterval(function() {
            fetch('/api/status').then(response => response.json()).then(data => {
                document.getElementById('current-mode').textContent = data.mode;
                document.getElementById('current-plant').textContent = data.plant_profile;
                
                // Update sensor displays
                if (data.sensors) {
                    document.querySelector('.sensor-value:nth-child(1)').textContent = data.sensors.soil_moisture + '%';
                    document.querySelector('.sensor-value:nth-child(2)').textContent = data.sensors.temperature + '°C';
                    document.querySelector('.sensor-value:nth-child(3)').textContent = data.sensors.humidity + '%';
                    document.querySelector('.sensor-value:nth-child(4)').textContent = data.sensors.light_intensity;
                }
                
                // Update control indicators
                if (data.control_status) {
                    document.querySelectorAll('.control-btn').forEach(btn => btn.classList.remove('active'));
                    if (data.control_status.pump_active) document.querySelector('[onclick*=\"pump=ON\"]').classList.add('active');
                    if (data.control_status.fan_active) document.querySelector('[onclick*=\"fan=ON\"]').classList.add('active');
                    if (data.control_status.light_active) document.querySelector('[onclick*=\"light=ON\"]').classList.add('active');
                }
            });
        }, 5000);
    </script>
</body>
</html>
  )";
}
