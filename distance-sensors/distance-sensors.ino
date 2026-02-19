#include <WiFiNINA.h>
#include <PubSubClient.h>
#include "config.h" // contains ssid, password, mqtt_server

WiFiClient wifiClient;
PubSubClient client(wifiClient);
const char* mqtt_topic  = "sensors/distance";

#define TRIG1 2
#define ECHO1 3
#define TRIG2 4
#define ECHO2 5
#define SOUND_SPEED 0.34  // mm per microsecond

unsigned long lastMsg = 0;
const unsigned long interval = 50; // 50Hz

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

// ---------------- MQTT ----------------
void reconnect() {
  // Use a unique client ID
  String clientId = "ArduinoUnoWiFi-" + String(random(0xffff), HEX);

  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect(clientId.c_str())) {
      Serial.println("connected!");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" trying again in 2 seconds");
      delay(2000);
    }
  }
}

// ---------------- Sensor ----------------
long readDistanceMM(int trigPin, int echoPin) {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  long duration = pulseIn(echoPin, HIGH, 20000); // 30ms timeout
  if (duration == 0) return -1; // no echo detected

  long distance = (duration * 343) / 2000; 
  return distance; 
}

// ---------------- Setup ----------------
void setup() {
  Serial.begin(9600);
  pinMode(TRIG1, OUTPUT);
  pinMode(ECHO1, INPUT);
  pinMode(TRIG2, OUTPUT);
  pinMode(ECHO2, INPUT);

  setup_wifi();
  client.setServer(mqtt_server, 1883);
  client.setBufferSize(256);
}

// ---------------- Loop ----------------
void loop() {
  if (WiFi.status() != WL_CONNECTED) setup_wifi();
  if (!client.connected()) reconnect();
  client.loop();

  unsigned long now = millis();
  if (now - lastMsg >= interval) {
    lastMsg = now;

    // Use 'long' to prevent the negative number overflow
    long x = readDistanceMM(TRIG1, ECHO1);
    delay(25); 
    long y = readDistanceMM(TRIG2, ECHO2);

    if (x < 0 || y < 0 || x > 4000 || y > 4000) {
      Serial.println("Invalid reading or out of range");
    } else {
      char payload[32];
      // Use %ld for 'long' integers
      snprintf(payload, sizeof(payload), "%ld,%ld", x, y);
      client.publish(mqtt_topic, payload);
      
      // Clear output for debugging
      Serial.print("Payload sent: ");
      Serial.println(payload);
      Serial.print("X: "); Serial.print(x); Serial.print("mm, ");
      Serial.print("Y: "); Serial.print(y); Serial.println("mm");
    }
  }
}
