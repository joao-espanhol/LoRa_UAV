import time
import csv
import re
import math
from pprint import pprint

# Criação da estrutura de armazenamento
armazenamento = {
    "DRONE": {
        "latitudes": [],
        "longitudes": [],
        "rssi": [],
        "hdop": [],
        "tempos": [],
        "pacotes_corrompidos": 0,
        "pacotes_validos": 0
    },
    "SOLO": {
        "latitudes": [],
        "longitudes": [],
        "rssi": [],
        "hdop": [],
        "tempos": [],
        "pacotes_corrompidos": 0,
        "pacotes_validos": 0
    },
}

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # raio da Terra em metros
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = math.sin(d_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

from pprint import pprint

def mostrar_analise(analise):
    print("\n===== ANÁLISE FINAL =====")
    print(f"Pacotes por receptor:")
    for rec, qtd in analise["pacotes_por_receptor"].items():
        print(f"  - {rec}: {qtd}")
    
    print("\nRSSI médio por receptor:")
    for rec, dados in analise["rssi_medio_por_receptor"].items():
        soma, cont = dados["soma"], dados["contagem"]
        rssi_medio = soma / cont if cont > 0 else None
        print(f"  - {rec}: {rssi_medio:.2f} dBm (baseado em {cont} pacotes)")

    print(f"\nMaior altitude registrada: {analise['maior_altitude']} m")

    print(f"\nDistância percorrida: {analise['distancia_percorrida'] / 1000:.2f} km")

    print("\nÚltimas posições (amostra):")
    for lat, lon, t in analise["ultimas_posicoes"][-5:]:  # últimas 5
        print(f"  - ({lat:.6f}, {lon:.6f}) @ {t}s")


# Criação da estrutura de análise
analise = {
    "pacotes_por_receptor": {},
    "rssi_medio_por_receptor": {},
    "maior_altitude": None,
    "ultimas_posicoes": [],
    "distancia_percorrida": 0.0
}

# Para ajuste caso o dia vire
ultimo_tempo = None
ajuste_dias = 0  

def converte_segundos(h, m, s):
    global ultimo_tempo, ajuste_dias
    segundos = h * 3600 + m * 60 + s

    if ultimo_tempo is not None and segundos < ultimo_tempo:
        # Virou o dia
        ajuste_dias += 86400  
    
    absoluto = segundos + ajuste_dias
    ultimo_tempo = segundos
    return absoluto


# Limites geográficos aproximados de São Paulo
LAT_MIN, LAT_MAX = -25.5, -19.5
LON_MIN, LON_MAX = -53.5, -44.0
ALT_MIN, ALT_MAX = 0, 10000

EXPECTED_DEVICE = "IFSPC@MPINAS"

def parse_linha(campos):
    
    if len(campos) != 9:
        return None, "Quantidade de campos diferente de 9"

    try:
        id_pack = int(campos[0])
        device = campos[1]
        lat = float(campos[2])
        lon = float(campos[3])
        hdop = float(campos[4])
        alt = float(campos[5])
        time_field = campos[6]
        hour, minute, second = map(int, time_field.split(':'))
        

        receptor_id = campos[7]
        rssi = int(campos[8])

        # Validações
        if device != EXPECTED_DEVICE:
            return None, f"Device inválido: {device}"
        if not (0 <= hour < 24 and 0 <= minute < 60 and 0 <= second < 60):
            return None, "Formato de hora inválido"
        if not (-120 <= rssi <= 0):
            return None, "Valor de RSSI fora do intervalo esperado"
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            return None, "Valores de latitude ou longitude fora do intervalo esperado"
        if hdop < 0:
            return None, "Valor de HDOP negativo"
        if not re.match(r'^[A-Za-z0-9@_]+$', receptor_id):
            return None, "Formato de receptor_id inválido"
        if not (LAT_MIN <= lat <= LAT_MAX):
            return None, f"Latitude fora do intervalo aceitável: {lat}"
        if not (LON_MIN <= lon <= LON_MAX):
            return None, f"Longitude fora do intervalo aceitável: {lon}"
        if not (ALT_MIN <= alt <= ALT_MAX):
            return None, f"Altitude fora do intervalo aceitável: {alt}"
        if receptor_id not in armazenamento:
            return None, f"Receptor_id desconhecido: {receptor_id}"
        if hdop > 20:  # HDOP muito alto
            return None, "HDOP muito alto"
        
        # Se passou por todas as validações, retorna o dicionário
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

arquivo_csv = "Testes30AGO.csv"

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

                    receptor = data_dict["receptor"]
                    lat = data_dict["lat"]
                    lon = data_dict["lon"]
                    rssi = data_dict["rssi"]
                    hdop = data_dict["hdop"]
                    tempo = converte_segundos(data_dict["hora"], data_dict["minuto"], data_dict["segundo"])
                    altitude = data_dict.get("alt", None)

                    # ---- Atualiza armazenamento bruto ----
                    armazenamento[receptor]["latitudes"].append(lat)
                    armazenamento[receptor]["longitudes"].append(lon)
                    armazenamento[receptor]["rssi"].append(rssi)
                    armazenamento[receptor]["hdop"].append(hdop)
                    armazenamento[receptor]["tempos"].append(tempo)

                    # ---- Atualiza análise ----
                    armazenamento[receptor]["pacotes_validos"] += 1

                    # Pacotes por receptor
                    analise["pacotes_por_receptor"].setdefault(receptor, 0)
                    analise["pacotes_por_receptor"][receptor] += 1


                    # RSSI médio incremental
                    if receptor not in analise["rssi_medio_por_receptor"]:
                        analise["rssi_medio_por_receptor"][receptor] = {"soma": 0, "contagem": 0}
                    analise["rssi_medio_por_receptor"][receptor]["soma"] += rssi
                    analise["rssi_medio_por_receptor"][receptor]["contagem"] += 1

                    # Maior altitude
                    if altitude is not None:
                        if analise["maior_altitude"] is None or altitude > analise["maior_altitude"]:
                            analise["maior_altitude"] = altitude

                    # Últimas posições (mantém só as últimas N, ex: 10)
                    analise["ultimas_posicoes"].append((lat, lon, tempo))
                    if len(analise["ultimas_posicoes"]) > 10:
                        analise["ultimas_posicoes"].pop(0)

                    # Distância percorrida (usando haversine incremental)
                    if len(analise["ultimas_posicoes"]) > 1:
                        lat1, lon1, t1 = analise["ultimas_posicoes"][-2]
                        lat2, lon2, t2 = analise["ultimas_posicoes"][-1]
                        analise["distancia_percorrida"] += haversine(lat1, lon1, lat2, lon2)

                else:
                    print(f"[INVALIDO] Linha descartada: {','.join(linha)} — Motivo: {erro}")

                    armazenamento[receptor]["pacotes_corrompidos"] += 1

            

            # Atualiza o offset para a próxima leitura
            if linahs_novas:
                offset = csvfile.tell()

                # 🔥 Impressão de teste após processar o batch
                print("\n==== RESUMO ====")
                print("Armazenamento:", armazenamento)
                print("Análise parcial:", analise)
                print("================\n")

                mostrar_analise(analise)
            else:
                time.sleep(3)

    except FileNotFoundError:
        print(f"[ERRO] Arquivo {arquivo_csv} não encontrado. Aguardando criação...")

    