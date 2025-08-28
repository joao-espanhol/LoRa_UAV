import serial
from datetime import datetime
import os

# ⚙️ CONFIGURAÇÕES
PORTA_SERIAL = '/dev/ttyUSB0'      # Altere conforme seu sistema
BAUD_RATE = 115200
PASTA_LOGS = 'logs_esp32'  # Pasta onde os logs serão salvos

os.makedirs(PASTA_LOGS, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
nome_arquivo = f"log_{timestamp}.txt"
caminho_arquivo = os.path.join(PASTA_LOGS, nome_arquivo)

try:
    with serial.Serial(PORTA_SERIAL, BAUD_RATE, timeout=1) as ser, open(caminho_arquivo, 'a') as f:
        print(f"Iniciando leitura da porta {PORTA_SERIAL}")
        print(f"Log sendo salvo em: {caminho_arquivo}\n")
        
        while True:
            linha = ser.readline().decode('utf-8', errors='ignore').strip()
            if linha:
                hora_lida = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                log_formatado = f"[{hora_lida}] {linha}"
                print(log_formatado)
                f.write(log_formatado + "\n")

except serial.SerialException as e:
    print(f"Erro na conexão serial: {e}")
except KeyboardInterrupt:
    print("\nLeitura encerrada pelo usuário.")
    print(f"Arquivo salvo em: {caminho_arquivo}")

