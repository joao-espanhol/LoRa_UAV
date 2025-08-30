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
csvfile = open("Testes30AGO.csv", "a", newline='')
csv_writer = csv.writer(csvfile)

# abrir o log de erros
errfile = open("Testes30AGO_pacotes.log", "a")

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
                print(f"[{addr}] {data}")

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
