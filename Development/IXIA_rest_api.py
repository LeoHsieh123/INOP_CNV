import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')


import requests
import urllib3
import json
import os
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ======== 使用者設定 ========
IP = "10.89.83.99"
API_KEY = "5878418bf3644745a59d2d2f52696668"  # 換成實際 key
HEADERS = {"X-Api-Key": API_KEY, "Accept": "application/json"}

# ======== 基本 HTTP 操作 ========
def get(endpoint):
    url = f"https://{IP}/chassis/api/v2/ixos/{endpoint}"
    r = requests.get(url, headers=HEADERS, verify=False)
    if r.status_code == 200:
        return r.json()
    else:
        print(f"❌ GET {endpoint} failed:", r.status_code, r.text)
        return []

def post(endpoint, payload=None):
    url = f"https://{IP}/chassis/api/v2/ixos/{endpoint}"
    r = requests.post(url, headers=HEADERS, json=payload or {}, verify=False)
    print(f"POST {endpoint}: {r.status_code}")
    try:
        print(json.dumps(r.json(), indent=2))
    except:
        print(r.text)
    return r

# ======== 顯示所有 port ========
def show_ports():
    ports = get("ports")
    if not ports:
        print("❌ 無法取得 Port 資訊")
        return
    print(f"\n📡 共有 {len(ports)} 個 Port：\n")
    print(f"{'ID':<6} {'Port':<6} {'Link':<6} {'Speed':<7} {'Type':<20} {'Manufacturer':<12} {'Model':<16}")
    print("-" * 90)
    for p in ports:
        port_id = p.get("id", "?")
        name = p.get("fullyQualifiedPortName", "?")
        link = p.get("linkState", "?")
        speed = p.get("speed", 0) / 1000
        ptype = p.get("type", "")
        manuf = p.get("transceiverManufacturer", "")
        model = p.get("transceiverModel", "")
        print(f"{port_id:<6} {name:<6} {link:<6} {speed:<6.0f}G {ptype:<20} {manuf:<12} {model:<16}")

# ======== Live Port Monitor ========
def live_port_monitor(interval=1):
    """持續更新所有 port 的即時狀態與流量統計"""
    try:
        ports = get("ports")
        port_map = {p["id"]: p for p in ports}
        print("📡 Start Live Port Monitor（Ctrl+C to Stop）...\n")
        time.sleep(1)

        while True:
            stats = get("portstats")   
            ''' stats
            'bytesReceived': 0, 
            'lastUpdatedUTC': '2025-11-08T06:29:30.835Z', 
            'framesSent': 0, 
            'fragments': 0, 
            'bytesSent': 0, 
            'id': 2175, 
            'validFramesReceived': 0, 
            'alignmentErrors': 0, 
            'parentId': 1106, 
            'crcErrors': 0
            '''
            os.system("cls" if os.name == "nt" else "clear")
            print(f"⏱️  {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'ID':<6} {'Port':<6} {'Link':<6} {'Speed':<7} {'Type':<18} {'Tx Bytes':>12} {'Rx Bytes':>12} {'CRC':>6}")
            print("-" * 80)
            for s in sorted(stats, key=lambda x: port_map.get(x.get("parentId"), {}).get("fullyQualifiedPortName", ""), reverse=False):
                pid = s.get("parentId")
                port = port_map.get(pid, {})
                name = port.get("fullyQualifiedPortName", "?")
                link = port.get("linkState", "?")
                speed = f"{port.get('speed', 0)//1000}G"
                ptype = port.get("type", "")
                tx = s.get("bytesSent", 0)
                rx = s.get("bytesReceived", 0)
                crc = s.get("crcErrors", 0)
                print(f"{pid:<6} {name:<6} {link:<6} {speed:<7} {ptype:<18} {tx:>12} {rx:>12} {crc:>6}")
            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n🛑 Stop monitoring")

# ======== 主選單 ========
def main_menu():
    live_port_monitor()

# ======== 程式入口 ========
if __name__ == "__main__":
    main_menu()
