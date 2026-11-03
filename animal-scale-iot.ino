#include <WiFi.h>
#include <PubSubClient.h>
#include "HX711.h"

#define DT  4
#define SCK 5

// ---------- WiFi e MQTT ----------
// Wokwi-GUEST é a rede simulada do Wokwi, com acesso à internet e sem senha.
const char* WIFI_SSID = "Wokwi-GUEST";
const char* WIFI_SENHA = "";

// Broker público do HiveMQ: sem usuário e senha. O tópico precisa ser único,
// porque qualquer pessoa conectada ao broker pode ler e publicar nele.
const char* MQTT_BROKER = "broker.hivemq.com";
const int MQTT_PORTA = 1883;
const char* MQTT_TOPICO = "clyvovet/fiap2026/balanca";

// ID do animal em T_CP_ANIMAIS (cadastro da API .NET).
// Na prática viria da tag RFID da coleira; na simulação, troque aqui para pesar outro animal.
const int ANIMAL_ID = 1;

// valor comum no Wokwi
float calibration_factor = 422.0;

HX711 scale;
WiFiClient wifi;
PubSubClient mqtt(wifi);

void conectarWifi() {
  Serial.print("Conectando ao WiFi");
  WiFi.begin(WIFI_SSID, WIFI_SENHA);
  while (WiFi.status() != WL_CONNECTED) {
    delay(250);
    Serial.print(".");
  }
  Serial.println(" conectado!");
}

void conectarMqtt() {
  while (!mqtt.connected()) {
    Serial.print("Conectando ao MQTT...");
    // client id aleatório: dois clientes com o mesmo id derrubam um ao outro no broker
    String clientId = "clyvovet-balanca-" + String(random(0xffff), HEX);
    if (mqtt.connect(clientId.c_str())) {
      Serial.println(" conectado!");
    } else {
      Serial.print(" falhou (estado ");
      Serial.print(mqtt.state());
      Serial.println("), tentando de novo em 2 s");
      delay(2000);
    }
  }
}

void setup() {
  Serial.begin(115200);

  Serial.println("Inicializando HX711...");
  scale.begin(DT, SCK);

  // PRIMEIRO zera
  scale.tare();

  // DEPOIS aplica escala
  scale.set_scale(calibration_factor);
  Serial.println("HX711 iniciado!");

  conectarWifi();
  mqtt.setServer(MQTT_BROKER, MQTT_PORTA);
}

void loop() {
  if (!mqtt.connected()) {
    conectarMqtt();
  }
  mqtt.loop();

  // leitura média
  float weight = scale.get_units(10);

  // remove negativos pequenos
  if (weight < 0) {
    weight = 0;
  }

  // formato: peso,animalId (ex.: 8.4,1). O Node-RED ignora 0 kg (balança vazia).
  String payload = String(weight, 1) + "," + String(ANIMAL_ID);

  mqtt.publish(MQTT_TOPICO, payload.c_str());
  Serial.println("Publicado: " + payload);

  delay(2000);
}
