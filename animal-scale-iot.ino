#include "HX711.h"

#define DT  4
#define SCK 5

HX711 scale;

String animalNames[6] = {
  "Jake",
  "Max",
  "Luna",
  "Bella",
  "Thor",
  "Mel"
};

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

  int randomIndex = random(0, 6);

  String payload =
    String(weight, 1) + "," +
    animalNames[randomIndex];

  Serial.println(payload);

  delay(2000);
}