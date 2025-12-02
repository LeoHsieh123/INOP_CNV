import argparse
import socket
import time

# ---------------------------------------------------
# Parse Arguments
# ---------------------------------------------------
parser = argparse.ArgumentParser()
parser.add_argument("--ip", type=str, required=True)      # ex: 10.89.83.26:8086
parser.add_argument("--slot", type=str, required=True)    # ex: 3
args = parser.parse_args()

# 拆解 IP:PORT
if ":" in args.ip:
    ip, port = args.ip.split(":")
    port = int(port)
else:
    ip = args.ip
    port = 8086   # default port if missing

slot_number = args.slot

print(f"[INFO] Connecting to DUT {ip}:{port}, slot {slot_number}")

# ---------------------------------------------------
# Connect to EthAgent
# ---------------------------------------------------
conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
conn.connect((ip, port))
print("Successfully connected to EthAgent")


'''
conn.sendall('INFOLIST:{}\n'.format(slot_number).encode())
conn.recv(65536).decode()
while 1:
    a = str(conn.recv(65536))
    print(a)
    b = a.find('ETRACK_ID:')
    c = a[b+13:b+21]
    print(c)
if 'OK\r\n' in a:
        break
'''

#conn.sendall('ADD {}\n'.format(slot_number).encode())
conn.sendall('ETHSPY:{} SUMMARY GET-STATUS\n'.format(slot_number).encode())

c = None

while 1:
    a = str(conn.recv(65536).decode())
    print(a)
    b = a.find('ETRACK-ID')
    if b != -1:  # Ensure 'ETRACK-ID' is found before slicing
        c = a[b+14:b+22]
        
    if 'OK\r\n' in a:
        break
    
    
conn.close()
print(c)
