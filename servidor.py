import socket
import re
import csv
import threading

HOST = '0.0.0.0'
PORT = 5000

# Locks para evitar escrita simultânea corromper arquivos
csv_lock = threading.Lock()
log_lock = threading.Lock()

# abrir arquivo CSV em modo append
csvfile = open("OPAN.csv", "a", newline='')
csv_writer = csv.writer(csvfile)

# abrir o log de erros
errfile = open("OPAN_pacotes.log", "a")

# --- Limites geográficos e dispositivo esperado ---
LAT_MIN, LAT_MAX = -25.5, -19.5
LON_MIN, LON_MAX = -53.5, -44.0
ALT_MIN, ALT_MAX = 0, 10000
EXPECTED_DEVICES = {"ALFA", "BRAVO", "CHARLIE"}
# --- Função de validação ---
def validar_linha_server(data_dict):
    try:
        device = data_dict["device"]
        lat = data_dict["lat"]
        lon = data_dict["lon"]
        hdop = data_dict["hdop"]
        alt = data_dict["alt"]
        rssi = data_dict["rssi"]
        receptor_id = data_dict["receptor_id"]
        time_field = data_dict["time"]
        hour, minute, second = map(int, time_field.split(':'))

        if device not in EXPECTED_DEVICES:
            return False, f"Device inválido: {device}"
        if not (0 <= hour < 24 and 0 <= minute < 60 and 0 <= second < 60):
            return False, "Formato de hora inválido"
        if not (-120 <= rssi <= 0):
            return False, "RSSI fora do intervalo"
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            return False, "Latitude ou longitude fora do intervalo"
        if not (LAT_MIN <= lat <= LAT_MAX):
            return False, f"Latitude fora do intervalo aceitável: {lat}"
        if not (LON_MIN <= lon <= LON_MAX):
            return False, f"Longitude fora do intervalo aceitável: {lon}"
        if not (ALT_MIN <= alt <= ALT_MAX):
            return False, f"Altitude fora do intervalo aceitável: {alt}"
        if hdop < 0:
            return False, "HDOP negativo"
        if hdop > 20:
            return False, "HDOP muito alto"
        if not re.match(r'^[A-Za-z0-9@_]+$', receptor_id):
            return False, f"Formato de receptor_id inválido: {receptor_id}"

        return True, None
    except Exception as e:
        return False, str(e)

def process_client(conn, addr):
    print(f"[+] Conectado por {addr}")
    with conn:
        while True:
            try:
                data = conn.recv(1024)
                if not data:
                    break

                text = data.decode('utf-8', errors='ignore')
                lines = text.splitlines()
                print(f"[{addr}] Recebido: {text.strip()}")

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

                            valid, error_msg = validar_linha_server(data_dict)
                            if valid:
                                with csv_lock:
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

                                print(f"[VALIDO] {addr} → {data_dict}")
                            else:
                                msg = f"{line.strip()} — {error_msg}\n"
                                print(f"[ERRO de validação] {addr}: {msg.strip()}")
                                with log_lock:
                                    errfile.write(msg)
                                    errfile.flush()

                        except Exception as e:
                            msg = f"{line.strip()} — {e}\n"
                            print(f"[ERRO ao converter dados] {addr}: {msg.strip()}")
                            with log_lock:
                                errfile.write(msg)
                                errfile.flush()
                    else:
                        msg = f"{line.strip()} — Campos insuficientes\n"
                        print(f"[ERRO] Pacote inválido {addr}: {line.strip()}")
                        with log_lock:
                            errfile.write(msg)
                            errfile.flush()

            except Exception as e:
                print(f"[ERRO] Cliente {addr}: {e}")
                break

    print(f"[-] Conexão encerrada: {addr}")


print(f"[*] Aguardando conexões na porta {PORT}...")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()

    while True:
        conn, addr = server.accept()
        t = threading.Thread(target=process_client, args=(conn, addr), daemon=True)
        t.start()
