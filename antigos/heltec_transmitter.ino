#include <SPI.h>
#include <LoRa.h>
#include <SSD1306Wire.h>
#include <TinyGPSPlus.h>
#include <HardwareSerial.h>

// Configurações GPS
#define GPS_BAUD 9600
#define GPS_RX   32
#define GPS_TX   33

TinyGPSPlus gps;
HardwareSerial GPSserial(2);
uint32_t lastSentenceMs = 0;
uint32_t lastReport = 0;
unsigned long reportInterval = 5000;

// Configurações OLED para Heltec ESP32 V2
#define SDA_OLED 4
#define SCL_OLED 15
#define RST_OLED 16

SSD1306Wire display(0x3c, SDA_OLED, SCL_OLED); // Fonte padrão
int counter = 0;

void printGPSTime() {
  if (gps.time.isValid() && gps.date.isValid()) {
    char buffer[32];
    sprintf(buffer, "%02d:%02d:%02d %02d/%02d/%04d",
            gps.time.hour(), gps.time.minute(), gps.time.second(),
            gps.date.day(), gps.date.month(), gps.date.year());
    display.drawString(0, 48, String(buffer));
  } else {
    display.drawString(0, 48, "Hora UTC: invalida");
  }
}

void logOLED(const String& linha1, const String& linha2 = "", const String& linha3 = "") {
  display.clear();
  display.setFont(ArialMT_Plain_10);
  display.drawString(0, 0, linha1);
  if (linha2 != "") display.drawString(0, 12, linha2);
  if (linha3 != "") display.drawString(0, 24, linha3);
  display.display();
}

void logBanner(const __FlashStringHelper* msg) {
  Serial.println(F("=============================="));
  Serial.println(msg);
  Serial.println(F("=============================="));
}

void printHDOPStatus(float hdop) {
  if (hdop == 0.0 || isnan(hdop)) {
 z   Serial.println(F("[GPS] HDOP inválido."));
    return;
  }

  Serial.print("[GPS] Qualidade do sinal (HDOP): ");
  Serial.print(hdop, 1);
  Serial.print(" → ");

  if (hdop <= 1.0) Serial.println(F("ÓTIMO"));
  else if (hdop <= 2.0) Serial.println(F("BOM"));
  else if (hdop <= 4.0) Serial.println(F("REGULAR"));
  else Serial.println(F("RUIM"));
}

void setup() {
  // Inicializa OLED
  pinMode(RST_OLED, OUTPUT);
  digitalWrite(RST_OLED, LOW);
  delay(50);
  digitalWrite(RST_OLED, HIGH);
  display.init();
  display.flipScreenVertically();
  
  logOLED("[TAREFA]", "Inicializando dispositivo...");
  logBanner(F("[TAREFA] Inicializando dispositivo..."));

  Serial.begin(115200);
  delay(1500);

  // Inicializa o LoRa
  Serial.println("[TAREFA] Iniciando LoRa...");
  logOLED("[TAREFA]", "Iniciando LoRa...");
  delay(1500);
  LoRa.setPins(18, 14, 26); // NSS, RST, DIO0
  if (!LoRa.begin(915E6)) {
    logOLED("[ERRO]", "LoRa não iniciado");
    logBanner(F("[ERRO] LoRa não iniciado"));
    while(1);
  }
  delay(1500);
  LoRa.setSpreadingFactor(12);
  Serial.println("[OK] LoRa iniciado.");
  logOLED("[OK]", "LoRa iniciado.", "Aguardando pacotes...");
  LoRa.setTxPower(20);
    
  // Inicializa GPS
  GPSserial.begin(GPS_BAUD, SERIAL_8N1, GPS_RX, GPS_TX);
  if (!GPSserial) {
    logBanner(F("[ERRO] Falha ao iniciar GPS - Verifique conexões"));
    logOLED("[ERRO]", "Falha ao iniciar GPS", "Verifique conexões");
    while(1);
  }
}

void loop() {
  Serial.println(F("\n--- RELATÓRIO GPS ---"));
  while (GPSserial.available()) {
    char c = GPSserial.read();
    gps.encode(c);
    lastSentenceMs = millis();
  }

  if (millis() - lastSentenceMs > 10000) {
    Serial.println(F("[ERRO] >10 s sem NMEA! Verifique conexão e antena."));
    lastSentenceMs = millis();
  }

  if (millis() - lastReport >= reportInterval) {
    lastReport = millis();

    if(gps.location.isValid()) {
      // Monta a mensagem LoRa
      String msg = String(counter++) + "[IFSPC@MPINAS]";

      // Envia via LoRa
      float lat = gps.location.lat();
      float lon = gps.location.lng();
      msg += "[" + String(lat) + "][" + String(lon) + "]";

      float sinal = 0.0;
      if (gps.hdop.isValid()) {
      sinal = gps.hdop.hdop();
        msg += "[" + String(sinal) + "]";
      }

      if (gps.altitude.isValid()) {
        msg += "[" + String(gps.altitude.meters(), 1) + "]";
      }

      if (gps.time.isValid()) {
        msg += "[";
        msg += String(gps.time.hour()) + ":" +
              String(gps.time.minute()) + ":" +
              String(gps.time.second()) + "]";
      }

      // Envia via LoRa
      LoRa.beginPacket();
      LoRa.print(msg);
      LoRa.endPacket();

      // Mostra resumo no OLED (linha por linha)
      String result = "[LoRa] pacote enviado \nLat: " + String(lat) + "\nLon: " + String(lon) + "\nSinal: " + String(sinal);
      logOLED(result);
      Serial.println("Enviado: " + msg);

      delay(3000); // Aguarda 3 segundos entre envios
    }
    else {
      String qsinal = "Qualidade do sinal: " + String(gps.hdop.hdop());
      logBanner(F("[ERRO] Localização do GPS inválida - Aguarde calibração"));
      printGPSTime();
      logOLED("[ERRO]", "Localização do GPS inválida", "Aguarde calibração\n" + qsinal);
    } 
  }
}
