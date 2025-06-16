#include <SPI.h>
#include <LoRa.h>
#include <SSD1306Wire.h>

// Configurações OLED para Heltec ESP32 V2
#define SDA_OLED 4
#define SCL_OLED 15
#define RST_OLED 16

SSD1306Wire display(0x3c, SDA_OLED, SCL_OLED); // Fonte padrão
int counter = 0;

// Gera string com N dígitos aleatórios
String generateRandomDigitString(int numDigits) {
  String result = "";
  for (int i = 0; i < numDigits; i++) {
    result += String(random(0, 10)); // dígito entre 0 e 9
  }
  return result;
}

void setup() {
  Serial.begin(115200);
  randomSeed(analogRead(0)); // Inicializa gerador de números aleatórios

  // Reset do OLED
  pinMode(RST_OLED, OUTPUT);
  digitalWrite(RST_OLED, LOW);
  delay(50);
  digitalWrite(RST_OLED, HIGH);

  // Inicializa o display
  display.init();
  display.clear();
  display.display();

  // Inicializa o LoRa
  LoRa.setPins(18, 14, 26); // NSS, RST, DIO0
  if (!LoRa.begin(915E6)) {
    display.clear();
    display.drawString(0, 0, "LoRa Fail!");
    display.display();
    while (1);
  }

  // Configura SF12 e potência máxima 20 dBm
  LoRa.setSpreadingFactor(12);
  LoRa.setTxPower(20);

  delay(1500);
}

void loop() {
  // Gera valores aleatórios como strings
  String vdigits = generateRandomDigitString(5);    // 5 dígitos
  String xdigits = generateRandomDigitString(10);   // 10 dígitos
  String xvdigits = generateRandomDigitString(15);  // 15 dígitos
  String xxdigits = generateRandomDigitString(20);  // 20 dígitos

  // Monta a mensagem LoRa
  String message = String(counter++) + "[IFSPC@MPINAS]," +
                   "[" + vdigits + "]" +
                   "[" + xdigits + "]" +
                   "[" + xvdigits + "]" +
                   "[" + xxdigits + "]" +
                   "[TCCLORA]";

  // Envia via LoRa
  LoRa.beginPacket();
  LoRa.print(message);
  LoRa.endPacket();

  // Mostra resumo no OLED (linha por linha)
  display.clear();
  display.drawString(0, 0, "ID: " + String(counter - 1));
  display.drawString(0, 10, "D5:  " + vdigits);
  display.drawString(0, 20, "D10: " + xdigits.substring(0, 10));
  display.drawString(0, 30, "D15: " + xvdigits.substring(0, 12));
  display.drawString(0, 40, "D20: " + xxdigits.substring(0, 12));
  display.drawString(0, 50, "Enviado!");
  display.display();

  // Também envia ao Serial Monitor
  Serial.println("Enviado: " + message);

  delay(3000); // Aguarda 3 segundos entre envios
}
