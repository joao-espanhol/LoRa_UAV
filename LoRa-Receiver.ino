#include <SPI.h>
#include <LoRa.h>
#include <SSD1306Wire.h>

// Definição dos pinos para Heltec ESP32 V2
#define SDA_OLED 4
#define SCL_OLED 15
#define RST_OLED 16

SSD1306Wire display(0x3c, SDA_OLED, SCL_OLED);

void setup() {
  Serial.begin(115200);
  while (!Serial);

  // Reset do display OLED
  pinMode(RST_OLED, OUTPUT);
  digitalWrite(RST_OLED, LOW);
  delay(50);
  digitalWrite(RST_OLED, HIGH);

  display.init();
  display.flipScreenVertically(); // Ajuste se necessário
  display.clear();
  display.drawString(0, 0, "LoRa Receiver");
  display.display();

  // Inicialização do LoRa
  LoRa.setPins(18, 14, 26); // NSS, RST, DIO0
  if (!LoRa.begin(915E6)) {
    display.clear();
    display.drawString(0, 0, "LoRa Init Fail!");
    display.display();
    while (1);
  }

  // Configura SF12 para receber corretamente
  LoRa.setSpreadingFactor(12);
}

void loop() {
  int packetSize = LoRa.parsePacket();
  if (packetSize) {
    String msg = "";
    while (LoRa.available()) {
      msg += (char)LoRa.read();
    }

    int rssi = LoRa.packetRssi();
    Serial.println("Recebido: " + msg);
    Serial.println("RSSI: " + String(rssi));

    // Parse básico da mensagem
    int idxStart = msg.indexOf('[');
    String id = msg.substring(0, idxStart);
    String d5 = getValue(msg, 1);
    String d10 = getValue(msg, 2);
    String d15 = getValue(msg, 3);
    String d20 = getValue(msg, 4);

    // Exibe no OLED formatado (como no sender)
    display.clear();
    display.drawString(0, 0, "ID: " + id);
    display.drawString(0, 10, "D5:  " + d5);
    display.drawString(0, 20, "D10: " + d10.substring(0, 10));
    display.drawString(0, 30, "D15: " + d15.substring(0, 12));
    display.drawString(0, 40, "D20: " + d20.substring(0, 12));
    display.drawString(0, 50, "RSSI: " + String(rssi));
    display.display();
  }
}

// Função auxiliar para extrair valores entre colchetes
String getValue(String data, int index) {
  int start = -1;
  int end = -1;
  int count = 0;

  for (int i = 0; i < data.length(); i++) {
    if (data.charAt(i) == '[') {
      if (count == index) start = i + 1;
      count++;
    } else if (data.charAt(i) == ']' && count == index + 1) {
      end = i;
      break;
    }
  }

  if (start != -1 && end != -1) {
    return data.substring(start, end);
  } else {
    return "";
  }
}
