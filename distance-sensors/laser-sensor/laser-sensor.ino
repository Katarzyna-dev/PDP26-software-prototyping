#include <Wire.h>
#include <VL53L0X.h>
#include <WiFiNINA.h>
#include <PubSubClient.h>
#include <WiFiUdp.h>
#include <NTPClient.h>
#include "config.h"

VL53L0X sensor;

WiFiClient wifiClient;
PubSubClient client(wifiClient);

const char* mqtt_topic = "sensors/distance";

unsigned long lastMsg = 0;
const unsigned long interval = 50; // 50Hz

// ----------- NTP -----------
WiFiUDP ntpUDP;
NTPClient timeClient(ntpUDP, "pool.ntp.org", 0, 60000);

// ---------------- WiFi ----------------
void setup_wifi() {
  Serial.print("Connecting to WiFi ");
  while (WiFi.begin(ssid, password) != WL_CONNECTED) {
    delay(200);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("WiFi connected, IP: ");
  Serial.println(WiFi.localIP());
}

// ----------- MQTT -----------
void reconnect() {
  String clientId = "VL53L0X-" + String(random(0xffff), HEX);

  while (!client.connected()) {
    if (client.connect(clientId.c_str())) {
      Serial.println("MQTT connected");
    } else {
      Serial.print("MQTT failed, rc=");
      Serial.println(client.state());
      delay(2000);
    }
  }
}

// ----------- Setup -----------
void setup() {
  Serial.begin(9600);

  Wire.begin();
  sensor.setTimeout(1000);

  if (!sensor.init()) {
    Serial.println("Failed to detect VL53L0X!");
    while (1);
  }

  sensor.startContinuous();

  setup_wifi();
  client.setServer(mqtt_server, 1883);
  client.setBufferSize(256);

  timeClient.begin();
}

// ----------- Loop -----------
void loop() {
  if (WiFi.status() != WL_CONNECTED) setup_wifi();
  if (!client.connected()) reconnect();
  client.loop();

  timeClient.update();

  unsigned long now = millis();
  if (now - lastMsg >= interval) {
    lastMsg = now;

    uint16_t distance = sensor.readRangeContinuousMillimeters();

    if (sensor.timeoutOccurred() || distance > 4000) {
      Serial.println("Invalid reading");
      return;
    }

    unsigned long epochTime = timeClient.getEpochTime();

    char payload[64];
    snprintf(payload, sizeof(payload), 
             "{\"distance\":%u,\"timestamp\":%lu}", 
             distance, epochTime);

    client.publish(mqtt_topic, payload);

    Serial.println(payload);
  }
}