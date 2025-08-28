#include <SPI.h>
#include <LoRa.h>
#include <SSD1306Wire.h>
#include <TinyGPSPlus.h>


// Configurações OLED para Heltec ESP32 V2
#define SDA_OLED 4
#define SCL_OLED 15
#define RST_OLED 16

SSD1306Wire display(0x3c, SDA_OLED, SCL_OLED); // Fonte padrão
int counter = 0;

// GPS
TinyGPSPlus gps;
HardwareSerial gpsSerial(2); // RX=16, TX=17

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
  gpsSerial.begin(9600, SERIAL_8N1, 16, 17);  // GPS RX, TX
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
  // Lê dados do GPS
  while (gpsSerial.available()) {
    gps.encode(gpsSerial.read());
  }

  // Gera valores aleatórios como strings
  String vdigits = generateRandomDigitString(5);    // 5 dígitos
  String xdigits = generateRandomDigitString(10);   // 10 dígitos
  String xvdigits = generateRandomDigitString(15);  // 15 dígitos
  String xxdigits = generateRandomDigitString(20);  // 20 dígitos

  // Coordenadas
  String latStr = gps.location.isValid() ? String(gps.location.lat(), 6) : "0.000000";
  String lonStr = gps.location.isValid() ? String(gps.location.lng(), 6) : "0.000000";

  // Monta a mensagem LoRa
  String message = String(counter++) + "[IFSPC@MPINAS]," +
                   "[" + vdigits + "]" +
                   "[" + xdigits + "]" +
                   "[" + xvdigits + "]" +
                   "[" + xxdigits + "]" +
                   "[TCCLORA]" +
                   "[LAT:" + latStr + "]" +
                   "[LON:" + lonStr + "]";

  // Envia via LoRa
  LoRa.beginPacket();
  LoRa.print(message);
  LoRa.endPacket();

// TELA 1: ID e primeiros dados
display.clear();
display.drawString(0, 0, "ID: " + String(counter - 1));
display.drawString(0, 10, "D5:  " + vdigits);
display.drawString(0, 20, "D10: " + xdigits.substring(0, 10));
display.drawString(0, 30, "Enviado!");
display.display();
delay(4000);

// TELA 2: dados complementares + GPS
display.clear();
display.drawString(0, 0, "ID: " + String(counter - 1));
display.drawString(0, 10, "D15: " + xvdigits.substring(0, 12));
display.drawString(0, 20, "D20: " + xxdigits.substring(0, 12));
display.drawString(0, 30, "LAT: " + latStr);
display.drawString(0, 40, "LON: " + lonStr);
display.display();
delay(4000);


  // Também envia ao Serial Monitor
  Serial.println("Enviado: " + message);

  delay(2000); // Aguarda 10 segundos entre envios
}
