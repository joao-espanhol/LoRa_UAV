import time
import csv
import re

# Device: letras, números, @ ou _
EXPECTED_DEVICE = "IFSPC@MPINAS"
def parse_linha(campos):
    
    if len(campos) != 9:
        return None, "Quantidade de campos diferente de 9"

    try:
        id_pack = int(campos[0])

        device = campos[1]
        if device != EXPECTED_DEVICE:
            return None, f"Device inválido: {device}"

        lat = float(campos[2])
        lon = float(campos[3])
        hdop = float(campos[4])
        alt = float(campos[5])

        time_field = campos[6]
        hour, minute, second = map(int, time_field.split(':'))
        if not (0 <= hour < 24 and 0 <= minute < 60 and 0 <= second < 60):
            return None, "Formato de hora inválido"

        receptor_id = campos[7]
        rssi = int(campos[8])

        if not (-120 <= rssi <= 0):
            return None, "Valor de RSSI fora do intervalo esperado"
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            return None, "Valores de latitude ou longitude fora do intervalo esperado"
        if hdop < 0:
            return None, "Valor de HDOP negativo"
        if alt < -500 or alt > 10000:
            return None, "Valor de altitude fora do intervalo esperado"
        if not re.match(r'^[A-Za-z0-9@_]+$', receptor_id):
            return None, "Formato de receptor_id inválido"
        data_dict = {
            "id_pack": id_pack,
            "device": device,
            "lat": lat,
            "lon": lon,
            "hdop": hdop,
            "alt": alt,
            "hora": hour,
            "minuto": minute,
            "segundo": second,
            "receptor": receptor_id,
            "rssi": rssi
        }
        return data_dict, None

    except Exception as e:
        return None, str(e)

arquivo_csv = "dados_validos.csv"

offset = 0
buffer_validas = []

while True:
    try:
        with open(arquivo_csv, "r") as csvfile:
            # Move o cursor para o último offset conhecido
            csvfile.seek(offset)
            reader = csv.reader(csvfile)

            linahs_novas = False
            for linha in reader:
                print("LINHA: {linha}")
                linahs_novas = True
                data_dict, erro = parse_linha(linha)
                if data_dict:
                    print(f"[VALIDO] {data_dict}")
                    buffer_validas.append(data_dict)

                else:
                    print(f"[INVALIDO] Linha descartada: {','.join(linha)} — Motivo: {erro}")


            # Atualiza o offset para a próxima leitura
            if linahs_novas:
                offset = csvfile.tell()
            else:
                time.sleep(3)

    except FileNotFoundError:
        print(f"[ERRO] Arquivo {arquivo_csv} não encontrado. Aguardando criação...")

    