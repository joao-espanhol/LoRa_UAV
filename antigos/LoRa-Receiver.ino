#include <SPI.h>
#include <LoRa.h>
#include <SSD1306Wire.h>
#include <WiFi.h>
#include <WiFiUdp.h>

// Definição dos pinos para Heltec ESP32 V2
#define SDA_OLED 4
#define SCL_OLED 15
#define RST_OLED 16

SSD1306Wire display(0x3c, SDA_OLED, SCL_OLED);

const char* ssid = "wifi";
const char* password = "Rondon@157";

const char* host_ip = "172.20.10.2";  // IP do seu PC na rede
const unsigned int port = 4210;         // Porta que o PC vai ouvir

WiFiUDP udp;


void setup() {
  Serial.begin(115200);
  while (!Serial);

  WiFi.begin(ssid, password);
  Serial.print("Conectando ao Wi-Fi");
    while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConectado!");
  Serial.println(WiFi.localIP());

  // Reset do display OLED
  pinMode(RST_OLED, OUTPUT);
  digitalWrite(RST_OLED, LOW);
  delay(50);
  digitalWrite(RST_OLED, HIGH);

  display.init();
  display.flipScreenVertically();
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

  LoRa.setSpreadingFactor(12);

  // >>> ADICIONADO <<<
  udp.begin(4211); // Porta local qualquer
}


void loop() {
  int packetSize = LoRa.parsePacket();
  if (packetSize) {
    String msg;
    msg.reserve(128); // reserva espaço na RAM para evitar fragmentação

    while (LoRa.available()) {
      msg += (char)LoRa.read();
    }

    int rssi = LoRa.packetRssi();


    Serial.println(msg);


    // Tentativa de parsing defensivo
    String id = msg.substring(0, msg.indexOf('['));
    String d5 = getValue(msg, 1);
    String d10 = getValue(msg, 2);
    String d15 = getValue(msg, 3);
    String d20 = getValue(msg, 4);
    String lat = getValue(msg, 6);
    String lon = getValue(msg, 7);

    if (lat.startsWith("LAT:")) lat = lat.substring(4);
    if (lon.startsWith("LON:")) lon = lon.substring(4);

    // Atualiza OLED (sem delay longo)
    mostrarTelaOLED1(id, d5, d10, rssi);
    delay(1000);  // pequena pausa entre telas

    mostrarTelaOLED2(d15, d20, lat, lon);
    delay(1000);

    // Envia para PC via UDP
    if (msg.length() > 0) {
      udp.beginPacket(host_ip, port);
      udp.write((const uint8_t*)msg.c_str(), msg.length());
      udp.endPacket();
      Serial.println("Pacote enviado para o PC.");
    }

    Serial.println("Latitude: " + lat);
    Serial.println("Longitude: " + lon);
  }
}

// Exibição em tela separada para clareza
void mostrarTelaOLED1(String id, String d5, String d10, int rssi) {
  display.clear();
  display.drawString(0, 0, "ID: " + id);
  display.drawString(0, 10, "D5: " + d5);
  display.drawString(0, 20, "D10:" + d10.substring(0, min(10, (int)d10.length())));
  display.drawString(0, 30, "RSSI: " + String(rssi));
  display.display();
}

void mostrarTelaOLED2(String d15, String d20, String lat, String lon) {
  display.clear();
  display.drawString(0, 0, "D15: " + d15.substring(0, min(12, (int)d15.length())));
  display.drawString(0, 10, "D20: " + d20.substring(0, min(12, (int)d20.length())));
  display.drawString(0, 20, "LAT: " + lat);
  display.drawString(0, 30, "LON: " + lon);
  display.display();
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
