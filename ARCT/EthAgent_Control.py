import argparse
import socket
import sys

# ---------------------------------------------------
# Parse Arguments
# ---------------------------------------------------
parser = argparse.ArgumentParser()
parser.add_argument("--ip", type=str, required=True)   # ex: 10.89.83.26:8086
parser.add_argument("--slot", type=str, required=True) # ex: 3
args = parser.parse_args()

# 拆解 IP:PORT
if ":" in args.ip:
    ip, port = args.ip.split(":")
    port = int(port)
else:
    ip = args.ip
    port = 8086

slot_number = args.slot

print(f"[INFO] Connecting to DUT {ip}:{port}", flush=True)

# ---------------------------------------------------
# Connect to EthAgent
# ---------------------------------------------------
conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
conn.connect((ip, port))
print("Successfully connected to EthAgent", flush=True)


# ---------------------------------------------------
# 完整回應聚合（一次印出完整 JSON + OK）
# ---------------------------------------------------
def recv_until_complete():
    buffer = ""
    json_started = False
    json_finished = False
    ok_received = False

    while True:
        raw = conn.recv(65536)
        if not raw:
            break

        text = raw.decode(errors="replace")
        buffer += text

        # 偵測 JSON 開始
        if "{" in text:
            json_started = True

        # 偵測 JSON 結束
        if "}" in text:
            json_finished = True

        # 偵測 OK
        if "OK" in text:
            ok_received = True

        # Case 1: JSON response (start + end + OK)
        if json_started and json_finished and ok_received:
            break

        # Case 2: non-JSON response (only OK)
        if not json_started and ok_received:
            break

    # 完整顯示（一次印出）
    print(buffer, flush=True)
    return buffer


# ---------------------------------------------------
# 初始化 Slot
# ---------------------------------------------------
conn.sendall(f"ADD {slot_number}\n".encode())
recv_until_complete()


# ---------------------------------------------------
# UI loop
# ---------------------------------------------------
while True:
    print("="*40, flush=True)
    print(
        " 1 - ADD slot\n",
        "2 - Release slot\n",
        "3 - GET-STATUS\n",
        "4 - GET-BANDWIDTH\n",
        "5 - Send transmit\n",
        "6 - Stop transmit\n",
        "7 - TX counter\n",
        "8 - RX counter\n",
        "9 - Clear counter",
        flush=True
    )
    print("="*40, flush=True)
    print("Select Action: ", flush=True)

    action = sys.stdin.readline().strip()

    # -------------------------------------------------------
    if action == "1":
        print("Slot:", flush=True)
        slot_number = sys.stdin.readline().strip()
        conn.sendall(f"ADD {slot_number}\n".encode())
        recv_until_complete()

    elif action == "2":
        conn.sendall(f"DEL {slot_number}\n".encode())
        recv_until_complete()

    elif action == "3":
        conn.sendall(f"ETHSPY:{slot_number} SUMMARY GET-STATUS\n".encode())
        recv_until_complete()

    elif action == "4":
        conn.sendall(f"ETHSPY:{slot_number} LINK GET-BANDWIDTH\n".encode())
        recv_until_complete()

    elif action == "5":
        conn.sendall(f"TX\n".encode())
        recv_until_complete()

    elif action == "6":
        conn.sendall(f"XX\n".encode())
        recv_until_complete()

    elif action == "7":
        conn.sendall(f"QT\n".encode())
        recv_until_complete()

    elif action == "8":
        conn.sendall(f"QR\n".encode())
        recv_until_complete()

    elif action == "9":
        conn.sendall(f"HC\n".encode())
        recv_until_complete()

    else:
        print("❌ Invalid option", flush=True)
