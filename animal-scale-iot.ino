#include "HX711.h"

#define DT  4
#define SCK 5

HX711 scale;

// ID do animal em T_CP_ANIMAIS (cadastro da API .NET).
// Na prática viria da tag RFID da coleira; na simulação, troque aqui para pesar outro animal.
const int ANIMAL_ID = 1;

// valor comum no Wokwi
float calibration_factor = 422.0;

void setup() {
  Serial.begin(115200);

  Serial.println("Inicializando HX711...");

  scale.begin(DT, SCK);

  // PRIMEIRO zera
  scale.tare();

  // DEPOIS aplica escala
  scale.set_scale(calibration_factor);

  Serial.println("HX711 iniciado!");
}

void loop() {

  // leitura média
  float weight = scale.get_units(10);

  // remove negativos pequenos
  if (weight < 0) {
    weight = 0;
  }

  // formato: peso,animalId (ex.: 8.4,1). O Node-RED ignora 0 kg (balança vazia).
  String payload =
    String(weight, 1) + "," +
    String(ANIMAL_ID);

  Serial.println(payload);

  delay(2000);
}
