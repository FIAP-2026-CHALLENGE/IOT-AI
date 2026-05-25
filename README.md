# Sistema de Monitoramento de Peso Animal com ESP32, MQTT, Node-RED e Oracle

## 📖 Sobre o Projeto

Este projeto simula um sistema IoT para monitoramento de peso de animais utilizando um ESP32 e um sensor BMP180.

O ESP32 realiza leituras do sensor, gera um valor fictício de peso e associa aleatoriamente um nome de animal.  
Os dados são enviados via MQTT no formato:

```txt
10.5,Jake
```

O fluxo no Node-RED:
1. Recebe os dados MQTT;
2. Trata as informações;
3. Exibe os dados em dashboard;
4. Salva automaticamente no banco Oracle.

---

# 🧠 Arquitetura do Projeto

```txt
ESP32 + BMP180
       ↓
     MQTT
       ↓
   Node-RED
       ↓
 Dashboard + Oracle Database
```

---

# 🛠 Tecnologias Utilizadas

## Hardware
- ESP32
- BMP180

## Software
- Arduino IDE
- Node-RED
- HiveMQ Cloud
- Oracle Database

---

# 📦 Estrutura dos Dados

Os dados são enviados no formato:

```txt
peso,nomeDoAnimal
```

Exemplo:

```txt
10.5,Jake
```

---

# ⚠️ Observação Importante

O BMP180 NÃO mede peso real.

Ele é um sensor de:
- pressão atmosférica;
- altitude;
- temperatura.

Neste projeto ele é utilizado apenas para fins acadêmicos/simulados.

Para medição real de peso, o ideal seria utilizar:
- célula de carga;
- módulo HX711.

---

# 🔌 Ligações do BMP180 no ESP32

| BMP180 | ESP32 |
|---|---|
| VCC | 3.3V |
| GND | GND |
| SDA | GPIO 21 |
| SCL | GPIO 22 |

---

# 🚀 Como Executar o Projeto

# 1️⃣ Configurar o Arduino IDE

Instale:
- ESP32 Board Package
- Biblioteca Adafruit BMP085
- Biblioteca Adafruit Unified Sensor

---

# 2️⃣ Código do ESP32

## 📄 main.ino

```cpp
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
```

---

# 3️⃣ Configurar o MQTT (HiveMQ)

Criar conta em:
- HiveMQ Cloud

Criar:
- Cluster MQTT;
- Usuário;
- Senha.

Configurar no ESP32 e no Node-RED.

---

# 4️⃣ Configurar o Node-RED

## 📥 Importar o fluxo JSON

No Node-RED:
1. Menu;
2. Import;
3. Cole o JSON do fluxo;
4. Deploy.

---

# 🔄 Funcionamento do Fluxo

## MQTT IN
Recebe os dados enviados pelo ESP32.

---

## Function

Transforma:

```txt
10.5,Jake
```

em:

```json
{
  "READING": 10.5,
  "ANIMAL": "Jake"
}
```

Código:

```javascript
const parts = msg.payload.split(',');

msg.payload = {
    READING: Number(parts[0]),
    ANIMAL: parts[1]
};

return msg;
```

---

## OracleDB

Executa o INSERT:

```sql
INSERT INTO T_EXAM_READING
(READING, ANIMAL, DATETIME)
VALUES
(:READING, :ANIMAL, SYSDATE)
```

---

## Dashboard

O Node-RED também exibe:
- gráfico em tempo real;
- gauge;
- debug das mensagens.

---

# 🗄 Estrutura da Tabela Oracle

```sql
CREATE TABLE T_EXAM_READING (
    ID NUMBER GENERATED ALWAYS AS IDENTITY,
    READING NUMBER(10,2),
    ANIMAL VARCHAR2(100),
    DATETIME DATE
);
```

---

# 📊 Exemplo de Fluxo Completo

## ESP32 envia:

```txt
12.4,Thor
```

## Node-RED transforma:

```json
{
  "READING": 12.4,
  "ANIMAL": "Thor"
}
```

## Oracle armazena:

| READING | ANIMAL | DATETIME |
|---|---|---|
| 12.4 | Thor | 24/05/2026 |

---

# ✅ Resultado Final

O sistema permite:
- leitura automática de sensores;
- envio de dados via MQTT;
- processamento em Node-RED;
- visualização em dashboard;
- persistência em banco Oracle.

---

# 👨‍💻 Autor

Projeto desenvolvido para fins acadêmicos e estudos de IoT com:
- ESP32;
- MQTT;
- Node-RED;
- Oracle Database.
