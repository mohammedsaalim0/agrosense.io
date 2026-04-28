/*
 * Smart IoT-Based Irrigation + Controlled Environment Growth Chamber
 * ESP32 Firmware with MQTT Integration
 * 
 * Hardware Configuration:
 * - ESP32-WROOM-32
 * - DHT22 (Temperature & Humidity) - GPIO32
 * - Capacitive Soil Moisture Sensor - GPIO34
 * - LDR Light Sensor - GPIO35
 * - Water Pump (via Relay) - GPIO26
 * - Cooling Fan (via MOSFET) - GPIO27
 * - Grow Light (via MOSFET) - GPIO25
 * - Humidifier (via MOSFET) - GPIO4
 * - Heater (via MOSFET) - GPIO33 (Optional)
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include <ESP32AnalogRead.h>

// WiFi Configuration
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// MQTT Configuration
const char* mqtt_server = "your-mqtt-broker.com";
const int mqtt_port = 1883;
const char* mqtt_username = "agrosense_user";
const char* mqtt_password = "your_mqtt_password";
const char* device_id = "chamber_001";

// Pin Definitions
#define DHT22_PIN 32
#define SOIL_MOISTURE_PIN 34
#define LDR_PIN 35
#define PUMP_RELAY_PIN 26
#define FAN_MOSFET_PIN 27
#define LIGHT_MOSFET_PIN 25
#define HUMIDIFIER_MOSFET_PIN 4
#define HEATER_MOSFET_PIN 33
#define STATUS_LED_PIN 2

// Actuator channels for PWM control
#define FAN_PWM_CHANNEL 0
#define LIGHT_PWM_CHANNEL 1
#define HUMIDIFIER_PWM_CHANNEL 2
#define HEATER_PWM_CHANNEL 3

// Global Variables
WiFiClient espClient;
PubSubClient client(espClient);
DHT dht(DHT22_PIN, DHT22::DHT22);

// Device State
struct DeviceState {
  // Sensor readings
  float temperature = 0.0;
  float humidity = 0.0;
  float soil_moisture = 0.0;
  float light_intensity = 0.0;
  
  // Actuator states
  bool pump_active = false;
  bool fan_active = false;
  bool light_active = false;
  bool humidifier_active = false;
  bool heater_active = false;
  
  int pump_power = 0;
  int fan_power = 0;
  int light_power = 0;
  int humidifier_power = 0;
  int heater_power = 0;
  
  // Control mode
  String control_mode = "auto";
  
  // Crop environment targets
  float target_temperature = 25.0;
  float target_humidity = 60.0;
  float target_moisture = 70.0;
  float target_light = 300.0;
  float temp_tolerance = 2.0;
  float humidity_tolerance = 5.0;
  float moisture_tolerance = 10.0;
  
  // Timing
  unsigned long last_sensor_read = 0;
  unsigned long last_mqtt_publish = 0;
  unsigned long pump_start_time = 0;
  unsigned long last_auto_control = 0;
} device_state;

// Safety and reliability
struct SafetyConfig {
  unsigned long max_pump_runtime = 600000; // 10 minutes
  unsigned long sensor_read_interval = 5000; // 5 seconds
  unsigned long mqtt_publish_interval = 10000; // 10 seconds
  float temperature_hysteresis = 0.5;
  float humidity_hysteresis = 2.0;
  float moisture_hysteresis = 3.0;
} safety;

void setup() {
  Serial.begin(115200);
  Serial.println("\n=== Smart IoT Chamber Starting ===");
  
  // Initialize pins
  initializePins();
  
  // Initialize PWM channels
  initializePWM();
  
  // Initialize DHT22 sensor
  dht.begin();
  
  // Connect to WiFi
  connectWiFi();
  
  // Initialize MQTT
  initializeMQTT();
  
  // Initialize device state
  initializeDeviceState();
  
  Serial.println("=== Smart IoT Chamber Ready ===");
}

void loop() {
  // Maintain MQTT connection
  if (!client.connected()) {
    reconnectMQTT();
  }
  client.loop();
  
  // Read sensors periodically
  if (millis() - device_state.last_sensor_read > safety.sensor_read_interval) {
    readSensors();
    device_state.last_sensor_read = millis();
  }
  
  // Publish sensor data periodically
  if (millis() - device_state.last_mqtt_publish > safety.mqtt_publish_interval) {
    publishSensorData();
    device_state.last_mqtt_publish = millis();
  }
  
  // Automatic control logic
  if (device_state.control_mode == "auto") {
    automaticControl();
  }
  
  // Safety checks
  safetyChecks();
  
  delay(100);
}

void initializePins() {
  // Output pins
  pinMode(PUMP_RELAY_PIN, OUTPUT);
  pinMode(FAN_MOSFET_PIN, OUTPUT);
  pinMode(LIGHT_MOSFET_PIN, OUTPUT);
  pinMode(HUMIDIFIER_MOSFET_PIN, OUTPUT);
  pinMode(HEATER_MOSFET_PIN, OUTPUT);
  pinMode(STATUS_LED_PIN, OUTPUT);
  
  // Input pins
  pinMode(SOIL_MOISTURE_PIN, INPUT);
  pinMode(LDR_PIN, INPUT);
  
  // Set initial states
  digitalWrite(PUMP_RELAY_PIN, LOW);
  digitalWrite(STATUS_LED_PIN, LOW);
  
  Serial.println("Pins initialized");
}

void initializePWM() {
  // Configure PWM channels for MOSFET control
  ledcSetup(FAN_PWM_CHANNEL, 5000, 8); // 5kHz, 8-bit resolution
  ledcSetup(LIGHT_PWM_CHANNEL, 5000, 8);
  ledcSetup(HUMIDIFIER_PWM_CHANNEL, 5000, 8);
  ledcSetup(HEATER_PWM_CHANNEL, 5000, 8);
  
  // Attach PWM channels to pins
  ledcAttachPin(FAN_MOSFET_PIN, FAN_PWM_CHANNEL);
  ledcAttachPin(LIGHT_MOSFET_PIN, LIGHT_PWM_CHANNEL);
  ledcAttachPin(HUMIDIFIER_MOSFET_PIN, HUMIDIFIER_PWM_CHANNEL);
  ledcAttachPin(HEATER_MOSFET_PIN, HEATER_PWM_CHANNEL);
  
  Serial.println("PWM channels initialized");
}

void initializeDeviceState() {
  // Set default targets
  device_state.target_temperature = 25.0;
  device_state.target_humidity = 60.0;
  device_state.target_moisture = 70.0;
  device_state.target_light = 300.0;
  device_state.control_mode = "auto";
  
  // Turn off all actuators initially
  setPumpState(false, 0);
  setFanState(false, 0);
  setLightState(false, 0);
  setHumidifierState(false, 0);
  setHeaterState(false, 0);
  
  Serial.println("Device state initialized");
}

void connectWiFi() {
  Serial.print("Connecting to WiFi...");
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nWiFi connection failed!");
  }
}

void initializeMQTT() {
  client.setServer(mqtt_server, mqtt_port);
  client.setCredentials(mqtt_username, mqtt_password);
  client.setCallback(mqttCallback);
  
  reconnectMQTT();
}

void reconnectMQTT() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    
    if (client.connect(device_id)) {
      Serial.println("MQTT connected!");
      
      // Subscribe to command topics
      String command_topic = String("agrosense/chamber/") + device_id + "/command/#";
      client.subscribe(command_topic.c_str());
      
      // Publish online status
      publishStatus();
      
    } else {
      Serial.print("MQTT connection failed, rc=");
      Serial.print(client.state());
      Serial.println(" trying again in 5 seconds");
      delay(5000);
    }
  }
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  Serial.print("MQTT Message [");
  Serial.print(topic);
  Serial.print("] ");
  
  // Parse topic
  String topic_str = String(topic);
  String base_topic = "agrosense/chamber/" + String(device_id) + "/command/";
  
  if (topic_str.startsWith(base_topic)) {
    String command = topic_str.substring(base_topic.length());
    
    // Parse JSON payload
    DynamicJsonDocument doc(1024);
    DeserializationError error = deserializeJson(doc, payload, length);
    
    if (!error) {
      handleCommand(command, doc);
    } else {
      Serial.print("JSON parse error: ");
      Serial.println(error.c_str());
    }
  }
}

void handleCommand(String command, JsonDocument& doc) {
  Serial.print("Handling command: ");
  Serial.println(command);
  
  if (command == "set_environment") {
    // Set crop environment targets
    if (doc.containsKey("temperature")) {
      device_state.target_temperature = doc["temperature"];
    }
    if (doc.containsKey("humidity")) {
      device_state.target_humidity = doc["humidity"];
    }
    if (doc.containsKey("moisture")) {
      device_state.target_moisture = doc["moisture"];
    }
    if (doc.containsKey("light")) {
      device_state.target_light = doc["light"];
    }
    if (doc.containsKey("tolerances")) {
      JsonObject tolerances = doc["tolerances"];
      if (tolerances.containsKey("temperature")) {
        device_state.temp_tolerance = tolerances["temperature"];
      }
      if (tolerances.containsKey("humidity")) {
        device_state.humidity_tolerance = tolerances["humidity"];
      }
      if (tolerances.containsKey("moisture")) {
        device_state.moisture_tolerance = tolerances["moisture"];
      }
    }
    
    Serial.println("Environment targets updated");
    publishStatus();
  }
  
  else if (command == "control_actuator") {
    // Manual actuator control
    String actuator = doc["actuator"];
    bool is_active = doc["is_active"];
    int power_level = doc["power_level"];
    
    if (actuator == "water_pump") {
      setPumpState(is_active, power_level);
    } else if (actuator == "cooling_fan") {
      setFanState(is_active, power_level);
    } else if (actuator == "grow_light") {
      setLightState(is_active, power_level);
    } else if (actuator == "humidifier") {
      setHumidifierState(is_active, power_level);
    } else if (actuator == "heater") {
      setHeaterState(is_active, power_level);
    }
    
    device_state.control_mode = "manual";
    publishStatus();
  }
  
  else if (command == "set_schedule") {
    // Handle irrigation schedule (simplified for this example)
    Serial.println("Schedule received (not implemented in this example)");
  }
  
  else if (command == "emergency_stop") {
    // Emergency stop all actuators
    emergencyStop();
  }
  
  else if (command == "reboot") {
    // Reboot device
    Serial.println("Reboot command received");
    delay(1000);
    ESP.restart();
  }
  
  else if (command == "get_status") {
    // Send current status
    publishStatus();
    publishSensorData();
  }
}

void readSensors() {
  // Read DHT22 (Temperature & Humidity)
  float temp_humidity = dht.readTemperature();
  float humidity = dht.readHumidity();
  
  if (!isnan(temp_humidity) && !isnan(humidity)) {
    device_state.temperature = temp_humidity;
    device_state.humidity = humidity;
  }
  
  // Read soil moisture (capacitive sensor)
  int soil_raw = analogRead(SOIL_MOISTURE_PIN);
  device_state.soil_moisture = map(soil_raw, 2800, 1200, 0, 100);
  device_state.soil_moisture = constrain(device_state.soil_moisture, 0, 100);
  
  // Read light intensity (LDR)
  int light_raw = analogRead(LDR_PIN);
  device_state.light_intensity = map(light_raw, 0, 4095, 0, 1000);
  device_state.light_intensity = constrain(device_state.light_intensity, 0, 1000);
  
  // Print sensor readings
  Serial.printf("Sensors - Temp: %.1f°C, Humidity: %.1f%%, Moisture: %.1f%%, Light: %.0f lux\n",
                device_state.temperature, device_state.humidity, 
                device_state.soil_moisture, device_state.light_intensity);
}

void publishSensorData() {
  DynamicJsonDocument doc(1024);
  
  // Sensor data
  JsonObject sensors = doc.createNestedObject("sensors");
  sensors["temperature"] = device_state.temperature;
  sensors["humidity"] = device_state.humidity;
  sensors["soil_moisture"] = device_state.soil_moisture;
  sensors["light"] = device_state.light_intensity;
  
  // Metadata
  doc["device_id"] = device_id;
  doc["timestamp"] = millis();
  doc["wifi_signal"] = WiFi.RSSI();
  doc["free_heap"] = ESP.getFreeHeap();
  
  String topic = "agrosense/chamber/" + String(device_id) + "/data/sensors";
  String message;
  serializeJson(doc, message);
  
  client.publish(topic.c_str(), message.c_str());
  Serial.println("Sensor data published");
}

void publishStatus() {
  DynamicJsonDocument doc(1024);
  
  // Actuator states
  JsonObject status = doc.createNestedObject("status");
  
  JsonObject pump = status.createNestedObject("water_pump");
  pump["is_active"] = device_state.pump_active;
  pump["power_level"] = device_state.pump_power;
  
  JsonObject fan = status.createNestedObject("cooling_fan");
  fan["is_active"] = device_state.fan_active;
  fan["power_level"] = device_state.fan_power;
  
  JsonObject light = status.createNestedObject("grow_light");
  light["is_active"] = device_state.light_active;
  light["power_level"] = device_state.light_power;
  
  JsonObject humidifier = status.createNestedObject("humidifier");
  humidifier["is_active"] = device_state.humidifier_active;
  humidifier["power_level"] = device_state.humidifier_power;
  
  JsonObject heater = status.createNestedObject("heater");
  heater["is_active"] = device_state.heater_active;
  heater["power_level"] = device_state.heater_power;
  
  // Metadata
  doc["device_id"] = device_id;
  doc["control_mode"] = device_state.control_mode;
  doc["timestamp"] = millis();
  
  String topic = "agrosense/chamber/" + String(device_id) + "/data/status";
  String message;
  serializeJson(doc, message);
  
  client.publish(topic.c_str(), message.c_str());
  Serial.println("Status published");
}

void setPumpState(bool is_active, int power_level) {
  device_state.pump_active = is_active;
  device_state.pump_power = constrain(power_level, 0, 100);
  
  if (is_active) {
    digitalWrite(PUMP_RELAY_PIN, HIGH);
    digitalWrite(STATUS_LED_PIN, HIGH);
    if (device_state.pump_start_time == 0) {
      device_state.pump_start_time = millis();
    }
    Serial.println("Pump turned ON");
  } else {
    digitalWrite(PUMP_RELAY_PIN, LOW);
    digitalWrite(STATUS_LED_PIN, LOW);
    device_state.pump_start_time = 0;
    Serial.println("Pump turned OFF");
  }
}

void setFanState(bool is_active, int power_level) {
  device_state.fan_active = is_active;
  device_state.fan_power = constrain(power_level, 0, 100);
  
  int pwm_value = map(power_level, 0, 100, 0, 255);
  ledcWrite(FAN_PWM_CHANNEL, is_active ? pwm_value : 0);
  
  Serial.printf("Fan: %s, Power: %d%%\n", 
              is_active ? "ON" : "OFF", device_state.fan_power);
}

void setLightState(bool is_active, int power_level) {
  device_state.light_active = is_active;
  device_state.light_power = constrain(power_level, 0, 100);
  
  int pwm_value = map(power_level, 0, 100, 0, 255);
  ledcWrite(LIGHT_PWM_CHANNEL, is_active ? pwm_value : 0);
  
  Serial.printf("Light: %s, Power: %d%%\n", 
              is_active ? "ON" : "OFF", device_state.light_power);
}

void setHumidifierState(bool is_active, int power_level) {
  device_state.humidifier_active = is_active;
  device_state.humidifier_power = constrain(power_level, 0, 100);
  
  int pwm_value = map(power_level, 0, 100, 0, 255);
  ledcWrite(HUMIDIFIER_PWM_CHANNEL, is_active ? pwm_value : 0);
  
  Serial.printf("Humidifier: %s, Power: %d%%\n", 
              is_active ? "ON" : "OFF", device_state.humidifier_power);
}

void setHeaterState(bool is_active, int power_level) {
  device_state.heater_active = is_active;
  device_state.heater_power = constrain(power_level, 0, 100);
  
  int pwm_value = map(power_level, 0, 100, 0, 255);
  ledcWrite(HEATER_PWM_CHANNEL, is_active ? pwm_value : 0);
  
  Serial.printf("Heater: %s, Power: %d%%\n", 
              is_active ? "ON" : "OFF", device_state.heater_power);
}

void automaticControl() {
  unsigned long current_time = millis();
  
  // Only run auto control every 10 seconds
  if (current_time - device_state.last_auto_control < 10000) {
    return;
  }
  
  device_state.last_auto_control = current_time;
  
  // Temperature control
  float temp_diff = device_state.temperature - device_state.target_temperature;
  if (temp_diff > device_state.temp_tolerance) {
    // Too hot - turn on fan
    setFanState(true, 75);
  } else if (temp_diff < -device_state.temp_tolerance) {
    // Too cold - turn on heater
    setHeaterState(true, 50);
  } else {
    // Within tolerance - turn off both
    setFanState(false, 0);
    setHeaterState(false, 0);
  }
  
  // Humidity control
  float humidity_diff = device_state.humidity - device_state.target_humidity;
  if (humidity_diff < -device_state.humidity_tolerance) {
    // Too dry - turn on humidifier
    setHumidifierState(true, 60);
  } else {
    // Within tolerance - turn off humidifier
    setHumidifierState(false, 0);
  }
  
  // Soil moisture control
  float moisture_diff = device_state.soil_moisture - device_state.target_moisture;
  if (moisture_diff < -device_state.moisture_tolerance) {
    // Too dry - turn on pump
    setPumpState(true, 80);
  } else {
    // Within tolerance - turn off pump
    setPumpState(false, 0);
  }
  
  // Light control (simplified - based on time)
  // In a real implementation, this would use sunrise/sunset times
  int current_hour = (current_time / 3600000) % 24;
  if (current_hour >= 6 && current_hour <= 22) {
    // Daytime - turn on light
    setLightState(true, 70);
  } else {
    // Nighttime - turn off light
    setLightState(false, 0);
  }
  
  Serial.println("Automatic control executed");
}

void safetyChecks() {
  // Check pump runtime
  if (device_state.pump_active && device_state.pump_start_time > 0) {
    unsigned long pump_runtime = millis() - device_state.pump_start_time;
    if (pump_runtime > safety.max_pump_runtime) {
      Serial.println("SAFETY: Pump runtime exceeded - turning off");
      setPumpState(false, 0);
      
      // Send safety alert
      DynamicJsonDocument alert(256);
      alert["alert_type"] = "safety_timeout";
      alert["message"] = "Pump runtime exceeded maximum limit";
      alert["severity"] = "warning";
      
      String topic = "agrosense/chamber/" + String(device_id) + "/data/alert";
      String message;
      serializeJson(alert, message);
      client.publish(topic.c_str(), message.c_str());
    }
  }
  
  // Check temperature extremes
  if (device_state.temperature > 40.0 || device_state.temperature < 5.0) {
    Serial.println("SAFETY: Extreme temperature detected");
    emergencyStop();
  }
  
  // Check humidity extremes
  if (device_state.humidity > 95.0 || device_state.humidity < 10.0) {
    Serial.println("SAFETY: Extreme humidity detected");
    emergencyStop();
  }
  
  // Check heap memory
  if (ESP.getFreeHeap() < 10000) {
    Serial.println("SAFETY: Low memory detected");
    DynamicJsonDocument alert(256);
    alert["alert_type"] = "memory_low";
    alert["message"] = "System memory critically low";
    alert["severity"] = "critical";
    
    String topic = "agrosense/chamber/" + String(device_id) + "/data/alert";
    String message;
    serializeJson(alert, message);
    client.publish(topic.c_str(), message.c_str());
  }
}

void emergencyStop() {
  Serial.println("EMERGENCY STOP ACTIVATED");
  
  // Turn off all actuators immediately
  setPumpState(false, 0);
  setFanState(false, 0);
  setLightState(false, 0);
  setHumidifierState(false, 0);
  setHeaterState(false, 0);
  
  // Set control mode to manual
  device_state.control_mode = "manual";
  
  // Send emergency alert
  DynamicJsonDocument alert(256);
  alert["alert_type"] = "emergency_stop";
  alert["message"] = "Emergency stop activated by system";
  alert["severity"] = "critical";
  
  String topic = "agrosense/chamber/" + String(device_id) + "/data/alert";
  String message;
  serializeJson(alert, message);
  client.publish(topic.c_str(), message.c_str());
  
  publishStatus();
}
