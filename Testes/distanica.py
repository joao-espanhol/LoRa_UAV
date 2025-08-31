import csv
import math

# ===== Coordenadas fixas da base (edite conforme necessário) =====
def dms_to_decimal(grau, minuto, segundo, hemisferio):
    dd = float(grau) + float(minuto)/60 + float(segundo)/3600
    return -dd if hemisferio.upper() in ("S","W") else dd

BASE_LAT = dms_to_decimal(22, 52, 24, "S") 
BASE_LON = dms_to_decimal(47, 6, 42, "W")   


def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # raio da Terra em metros
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = math.sin(d_phi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(d_lambda/2)**2
    c = 2*math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def gerar_csv_com_distancia(arquivo_entrada, arquivo_saida):
    # ordem fixa das colunas do seu CSV
    colunas = ["id_pack", "device", "lat", "lon", "hdop", "alt", "time", "receptor", "rssi"]

    with open(arquivo_entrada, "r", newline="") as infile:
        reader = csv.DictReader(infile, fieldnames=colunas)
        
        fieldnames = colunas + ["distancia"]

        with open(arquivo_saida, "w", newline="") as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in reader:
                try:
                    lat = float(row["lat"])
                    lon = float(row["lon"])
                    dist = haversine(BASE_LAT, BASE_LON, lat, lon)
                    row["distancia"] = round(dist, 2)
                except ValueError:
                    row["distancia"] = ""
                writer.writerow(row)

if __name__ == "__main__":
    entrada = "Testes30AGO copy.csv"
    saida = "Testes30AGODIST copy.csv"
    gerar_csv_com_distancia(entrada, saida)
    print(f"Arquivo '{saida}' gerado com sucesso!")
