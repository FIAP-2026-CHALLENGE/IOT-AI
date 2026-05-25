#include "HX711.h"

// ============================
// PINOS HX711
// ============================
#define DT  4
#define SCK 5

HX711 scale;

// ============================
// NOMES DOS ANIMAIS
// ============================
String animalNames[6] = {
  "Jake",
  "Max",
  "Luna",
  "Bella",
  "Thor",
  "Mel"
};

// ============================
// FATOR DE CALIBRAÇÃO
// ============================
//
// VOCÊ PRECISA AJUSTAR ESSE VALOR
// conforme sua célula de carga.
//
// Exemplo:
// -7050
// 2280
// -430
//
float calibration_factor = 0.0;

// ============================

void setup() {
  Serial.begin(115200);

  Serial.println("Inicializando HX711...");

  // Inicializa HX711
  scale.begin(DT, SCK);

  // Define fator de calibração
  scale.set_scale(calibration_factor);

  // Zera balança
  scale.tare();

  Serial.println("HX711 iniciado com sucesso!");
  Serial.println("Balança zerada!");

  randomSeed(millis());
}

void loop() {

  // ============================
  // LEITURA DO PESO
  // ============================

  // Média de 10 leituras
  float weight = scale.get_units(10);

  // Evita negativos pequenos
  if (weight < 0) {
    weight = 0;
  }

  // ============================
  // NOME ALEATÓRIO
  // ============================

  int randomIndex = random(0, 6);

  String animalName = animalNames[randomIndex];

  // ============================
  // PAYLOAD
  // ============================

  // Formato:
  // peso,nome
  //
  // Exemplo:
  // 10.5,Jake

  String payload = String(weight, 1) + "," + animalName;

  // ============================
  // ENVIO SERIAL
  // ============================

  Serial.println(payload);

  delay(5000);
}