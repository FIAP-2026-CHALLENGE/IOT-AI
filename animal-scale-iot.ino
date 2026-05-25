#include <Wire.h>
#include <Adafruit_BMP085.h>

Adafruit_BMP085 bmp;

// Lista de nomes dos animais
String animalNames[6] = {
  "Jake",
  "Max",
  "Luna",
  "Bella",
  "Thor",
  "Mel"
};

void setup() {
  Serial.begin(115200);

  // Inicializa I2C
  Wire.begin(21, 22);

  // Inicializa BMP180
  if (!bmp.begin()) {
    Serial.println("BMP180 nao encontrado!");
    
    while (1) {
      delay(1000);
    }
  }

  Serial.println("BMP180 iniciado com sucesso!");
  
  // Gera números aleatórios
  randomSeed(millis());
}

void loop() {

  // Leitura da pressão
  float pressure = bmp.readPressure();

  /*
    Exemplo de conversão fictícia:
    Aqui estamos apenas simulando um peso.
  */

  float weight = (pressure / 10000.0);

  // Limita para algo mais realista
  weight = weight - 90;

  if (weight < 1) {
    weight = random(1, 15);
  }

  // Escolhe nome aleatório
  int randomIndex = random(0, 6);

  String animalName = animalNames[randomIndex];

  // Formato:
  // numero,nomeDoAnimal
  String payload = String(weight, 1) + "," + animalName;

  // Envia pela Serial
  Serial.println(payload);

  delay(5000);
}