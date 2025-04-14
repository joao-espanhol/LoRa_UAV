#include <LoRa.h>
#include <SPI.h>

/* Definições para comunicação com rádio LoRa */
#define SCK_LORA        5
#define MISO_LORA       19
#define MOSI_LORA       27
#define RESET_PIN_LORA  14
#define SS_PIN_LORA     18
#define DIO0_PIN_LORA   26  // Corrigido

#define HIGH_GAIN_LORA  20
#define BAND            915E6

#define DEBUG_SERIAL_BAUDRATE 115200

long informacao_a_ser_enviada = 0;

bool init_comunicacao_lora(void) {
    bool status_init = false;
    Serial.println("[LoRa Sender] Tentando iniciar comunicacao com o radio LoRa...");
    SPI.begin(SCK_LORA, MISO_LORA, MOSI_LORA, SS_PIN_LORA);
    LoRa.setPins(SS_PIN_LORA, RESET_PIN_LORA, DIO0_PIN_LORA);

    if (!LoRa.begin(BAND)) {
        Serial.println("[LoRa Sender] Falhou. Nova tentativa em 1 segundo...");
        delay(1000);
    } else {
        LoRa.setTxPower(HIGH_GAIN_LORA);
        Serial.println("[LoRa Sender] Comunicacao OK");
        status_init = true;
    }

    return status_init;
}

void setup() {
    Serial.begin(DEBUG_SERIAL_BAUDRATE);
    while (!Serial);

    while (!init_comunicacao_lora());
}

void loop() {
    LoRa.beginPacket();
    LoRa.write((unsigned char *)&informacao_a_ser_enviada, sizeof(informacao_a_ser_enviada));
    LoRa.endPacket();

    Serial.print("[LoRa Sender] Enviado: ");
    Serial.println(informacao_a_ser_enviada);

    informacao_a_ser_enviada++;
    delay(1000);
}
