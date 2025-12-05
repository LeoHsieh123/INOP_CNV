import socket
import time

ip = '10.89.83.236'

ip_port = 8086
conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
addr= (ip,ip_port)
conn.connect(addr)
print("Successfully connected to EthAgent")
slot_number= "3"

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
