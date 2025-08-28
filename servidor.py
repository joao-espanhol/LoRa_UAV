import socket
import math
import re
import csv
import os


HOST = '0.0.0.0'
PORT = 5000

# def haversine(lat1, lon1, lat2, lon2):
#     R = 6371000  # raio da Terra em metros
#     phi1 = math.radians(lat1)
#     phi2 = math.radians(lat2)
#     d_phi = math.radians(lat2 - lat1)
#     d_lambda = math.radians(lon2 - lon1)

#     a = math.sin(d_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2.0) ** 2
#     c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
#     return R * c

# lat_list = []
# lon_list = []

# abrir arquivo CSV em modo append

csvfile = open("dados_validos.csv", "a", newline='')
csv_writer = csv.writer(csvfile)

# abrir o log de erros
errfile = open("pacotes_invalidos.log", "a")


print(f"[*] Aguardando conexão na porta {PORT}...")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:

    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(1)
    conn, addr = server.accept()
    print(f"[+] Conectado por {addr}")

    with conn:
        while True:
            data = conn.recv(1024)
            if not data:
                break

            try:
                # Decodifica e processa os dados recebidos
                text = data.decode('utf-8')
                # Separa linhas caso venha mais de uma por pacote
                lines = text.splitlines()
                print(data)

                for line in lines:

                    pattern = r"\[(.*?)\]"
                    matches = re.findall(pattern, line)
                    if len(matches) >= 8:
                        try:
                            data_dict = {
                                "id_pack": int(line.split("[")[0]),
                                "device": matches[0],
                                "lat": float(matches[1]),
                                "lon": float(matches[2]),
                                "hdop": float(matches[3]),
                                "alt": float(matches[4]),
                                "time": matches[5],
                                "receptor_id": matches[6],
                                "rssi": int(matches[7]),
                            }
                            csv_writer.writerow([
                                    data_dict["id_pack"],
                                    data_dict["device"],
                                    data_dict["lat"],
                                    data_dict["lon"],
                                    data_dict["hdop"],
                                    data_dict["alt"],
                                    data_dict["time"],
                                    data_dict["receptor_id"],
                                    data_dict["rssi"]
                            ])
                            csvfile.flush()
                            print(f"[VALIDO] {data_dict}")

                        except Exception as e:
                            print(f"[ERRO ao converter dados]: '{line.strip()}' — {e}")
                            errfile.write(f"{line.strip()} — {e}\n")
                            errfile.flush()

                    else:
                        print(f"[ERRO] Pacote inválido: '{line.strip()}'")
                        errfile.write(f"{line.strip()} — Campos insuficientes\n")
                        errfile.flush()


            except Exception as e:
                print(f"[ERRO] Decodificação: {e}")

                    # if "Lat:" in line and "Lon:" in line:
                    #     try:
                    #         lat_str = line.split("Lat:")[1].split("Lon:")[0].strip()
                    #         lon_str = line.split("Lon:")[1].strip()
                    #         lat = float(lat_str)
                    #         lon = float(lon_str)

                    #         lat_list.append(lat)
                    #         lon_list.append(lon)

                    #         print(f"Data: {data}\nPosição recebida: Latitude = {lat:.6f}, Longitude = {lon:.6f}")

                    #         if len(lat_list) % 10 == 0:
                    #             avg_lat = sum(lat_list) / len(lat_list)
                    #             avg_lon = sum(lon_list) / len(lon_list)

                    #             errors = [haversine(avg_lat, avg_lon, lt, ln) for lt, ln in zip(lat_list, lon_list)]
                    #             std_total = statistics.stdev(errors)

                    #             delta_lat_m = [(lt - avg_lat) * 111320 for lt in lat_list]
                    #             delta_lon_m = [(ln - avg_lon) * 111320 * math.cos(math.radians(avg_lat)) for ln in lon_list]
                    #             std_lat_m = statistics.stdev(delta_lat_m)
                    #             std_lon_m = statistics.stdev(delta_lon_m)

                    #             print(f"  Após {len(lat_list)} posições:")
                    #             print(f"      STD Latitude  (m): {std_lat_m:.2f}")
                    #             print(f"      STD Longitude (m): {std_lon_m:.2f}")
                    #             print(f"      STD Total     (m): {std_total:.2f}\n")

                    #     except Exception as e:
                    #         print(f"[ERRO ao processar linha GPS]: '{line.strip()}' — {e}")
