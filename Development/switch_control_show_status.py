import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')


import time, os
from netmiko import ConnectHandler

LOG_FILE = "switch_log.txt"
if os.path.exists(LOG_FILE):
    os.remove(LOG_FILE)

def log_command(cmd, result):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] >>> {cmd}\n")
        f.write(result)
        f.write("\n" + "="*100 + "\n")

def show_loop(net_connect, port, interval, detail=True):
    print(f"🚀 Monitoring ethernet {port}/1 (Press Ctrl+C to stop)\n")
    cmd = f"show interface ethernet {port}/1" if detail else f"show interface ethernet {port}/1 status"
    try:
        while True:
            output = net_connect.send_command_timing(cmd)
            os.system('cls' if os.name == 'nt' else 'clear')
            print("="*120)
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {cmd}")
            print("="*120)
            print(output)
            log_command(cmd, output)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n🛑 Stop monitor\n")

def connect_arista(ip, user, pwd):
    arista = {
        'device_type': 'arista_eos',
        'ip': ip,
        'username': user,
        'password': pwd,
    }
    print(f"🔌 Connecting to {ip} ...")
    net_connect = ConnectHandler(**arista)
    net_connect.enable()
    print("✅ Connected successfully!\n")
    return net_connect

# ---------------- MAIN ----------------
if __name__ == "__main__":
    net_connect = connect_arista("10.89.83.55", "admin", "Intel@123")

    port = input("Please select Arista Switch Port (ex: 13): ").strip()
    interval = 0.1
    show_loop(net_connect, port, interval, detail=True)