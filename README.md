# Sistema IoT de Pesagem Animal com ESP32, HX711, MQTT, Node-RED e Oracle

## 📖 Sobre o Projeto

Este projeto consiste em um sistema IoT para monitoramento de peso animal utilizando:

- ESP32;
- Sensor HX711;
- Célula de carga de 50kg;
- MQTT;
- Node-RED;
- Oracle Database.

O sistema realiza:
1. leitura do peso do animal através da célula de carga;
2. geração de um nome aleatório para simular diferentes animais;
3. envio dos dados via MQTT;
4. processamento dos dados no Node-RED;
5. armazenamento automático no banco Oracle;
6. visualização em dashboard em tempo real.

---

# 🧠 Arquitetura do Sistema

```txt
Célula de Carga
        ↓
      HX711
        ↓
      ESP32
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
- HX711
- Célula de carga 50kg

## Software
- Arduino IDE
- Node-RED
- HiveMQ Cloud
- Oracle Database

---

# 📦 Formato dos Dados

Os dados enviados seguem o padrão:

```txt
peso,nomeDoAnimal
```

Exemplo:

```txt
10.5,Jake
```

---

# 🔌 Ligações HX711 → ESP32

| HX711 | ESP32 |
|---|---|
| VCC | 3.3V |
| GND | GND |
| DT | GPIO 4 |
| SCK | GPIO 5 |

---

# 📚 Bibliotecas Necessárias

Instalar na Arduino IDE:

- HX711 Library (Bogde)

---

# 🚀 Como Executar o Projeto

# 1️⃣ Configurar Arduino IDE

## Instalar ESP32 Board

Na Arduino IDE:
1. Abra:
   - Arquivo → Preferências
2. Adicione:
   
```txt
https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
```

3. Vá em:
   - Ferramentas → Placa → Gerenciador de Placas
4. Instale:
   - ESP32 by Espressif Systems

---

# 2️⃣ Instalar Biblioteca HX711

Na Arduino IDE:
1. Sketch → Incluir Biblioteca → Gerenciar Bibliotecas
2. Pesquise:
   
```txt
HX711
```

3. Instale:
- HX711 by Bogde

---

# 3️⃣ Código do ESP32

## 📄 main.ino

```cpp
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
```

---

# ⚖️ Calibrando a Célula de Carga

O valor:

```cpp
float calibration_factor = 0.0;
```

precisa ser ajustado conforme sua célula de carga.

## Processo de calibração

1. Execute o código;
2. Abra o Serial Monitor;
3. Coloque um peso conhecido sobre a balança;
4. Ajuste o valor do `calibration_factor` até a leitura ficar correta.

Exemplo:

```cpp
float calibration_factor = -7050.0;
```

ou:

```cpp
float calibration_factor = 2280.0;
```

O valor varia conforme:
- célula de carga;
- montagem física;
- orientação dos fios.

---

# 4️⃣ Configurar o MQTT (HiveMQ)

Criar conta no HiveMQ Cloud.

Configurar:
- cluster MQTT;
- usuário;
- senha.

Utilizar as mesmas credenciais:
- no ESP32;
- no Node-RED.

---

# 5️⃣ Configurar o Node-RED

## Importar o fluxo JSON

1. Abra o Node-RED;
2. Clique no menu;
3. Import;
4. Cole o JSON do fluxo;
5. Deploy.

---

# 🔄 Funcionamento do Fluxo

## MQTT IN

Recebe os dados enviados pelo ESP32.

Exemplo recebido:

```txt
10.5,Jake
```

---

## Function

Transforma os dados em objeto JSON.

Código:

```javascript
const parts = msg.payload.split(',');

msg.payload = {
    READING: Number(parts[0]),
    ANIMAL: parts[1]
};

return msg;
```

Resultado:

```json
{
  "READING": 10.5,
  "ANIMAL": "Jake"
}
```

---

## OracleDB

O Node-RED executa automaticamente:

```sql
INSERT INTO T_EXAM_READING
(READING, ANIMAL, DATETIME)
VALUES
(:READING, :ANIMAL, SYSDATE)
```

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

# 📊 Dashboard

O dashboard do Node-RED exibe:
- gráfico em tempo real;
- gauge de peso;
- debug das mensagens;
- retorno Oracle.

---

# 📈 Exemplo de Fluxo Completo

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
- monitoramento automático de peso;
- integração IoT com MQTT;
- processamento em tempo real;
- visualização em dashboard;
- persistência em Oracle Database.

---

# 👨‍💻 Objetivo Acadêmico

Projeto desenvolvido para estudos de:
- IoT;
- sensores;
- MQTT;
- Node-RED;
- Oracle Database;
- integração entre hardware e software.

---

#### [Video no youtube](https://youtu.be/CoorQwypCCo)