#include <LoRa.h>
#include <SPI.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

/* Definições para LoRa */
#define SCK_LORA        5
#define MISO_LORA       19
#define MOSI_LORA       27
#define RESET_PIN_LORA  14
#define SS_PIN_LORA     18
#define DIO0_PIN_LORA   26

#define HIGH_GAIN_LORA  20
#define BAND            915E6

/* Definições do OLED */
#define OLED_SDA_PIN    4
#define OLED_SCL_PIN    15
#define SCREEN_WIDTH    128
#define SCREEN_HEIGHT   64
#define OLED_ADDR       0x3C
#define OLED_RESET      16

#define OLED_LINE1      0
#define OLED_LINE2      10
#define OLED_LINE3      20

#define DEBUG_SERIAL_BAUDRATE 115200

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

void display_init() {
    if (!display.begin(SSD1306_SWITCHCAPVCC, OLED_ADDR)) {
        Serial.println("[LoRa Receiver] Falha ao inicializar OLED");
    } else {
        Serial.println("[LoRa Receiver] OLED OK");
        display.clearDisplay();
        display.setTextSize(1);
        display.setTextColor(WHITE);
    }
}

bool init_comunicacao_lora() {
    bool status_init = false;
    Serial.println("[LoRa Receiver] Tentando iniciar LoRa...");
    SPI.begin(SCK_LORA, MISO_LORA, MOSI_LORA, SS_PIN_LORA);
    LoRa.setPins(SS_PIN_LORA, RESET_PIN_LORA, DIO0_PIN_LORA);

    if (!LoRa.begin(BAND)) {
        Serial.println("[LoRa Receiver] Falhou. Tentando novamente...");
        delay(1000);
    } else {
        LoRa.setTxPower(HIGH_GAIN_LORA);
        Serial.println("[LoRa Receiver] Comunicacao OK");
        status_init = true;
    }

    return status_init;
}

void setup() {
    Serial.begin(DEBUG_SERIAL_BAUDRATE);
    while (!Serial);

    Wire.begin(OLED_SDA_PIN, OLED_SCL_PIN);
    display_init();

    display.clearDisplay();
    display.setCursor(0, OLED_LINE1);
    display.print("Aguardando...");
    display.display();

    while (!init_comunicacao_lora());
}

void loop() {
    int packet_size = LoRa.parsePacket();

    if (packet_size == sizeof(long)) {
        long informacao_recebida = 0;
        char *ptr = (char *)&informacao_recebida;
        while (LoRa.available()) {
            *ptr++ = (char)LoRa.read();
        }

        int rssi = LoRa.packetRssi();

        display.clearDisplay();
        display.setCursor(0, OLED_LINE1);
        display.print("RSSI: ");
        display.println(rssi);
        display.setCursor(0, OLED_LINE2);
        display.print("Info: ");
        display.setCursor(0, OLED_LINE3);
        display.println(informacao_recebida);
        display.display();

        Serial.print("[LoRa Receiver] Info recebida: ");
        Serial.println(informacao_recebida);
    }
}
