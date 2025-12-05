import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import requests
import urllib3
import json
import time
import select
import traceback

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ======== 使用者設定 ========
IP = "10.89.83.99"
API_KEY = "5878418bf3644745a59d2d2f52696668"
HEADERS = {"X-Api-Key": API_KEY, "Accept": "application/json"}

REFRESH_INTERVAL = 0.2   # 每秒刷新一次

# ======== 安全 print（避免亂碼崩潰） ========
def safe_print(msg):
    try:
        print(msg, flush=True)
    except:
        try:
            print(msg.encode("utf-8", "replace").decode("utf-8"), flush=True)
        except:
            pass

# ======== 基本 HTTP 操作 ========
def get(endpoint):
    url = f"https://{IP}/chassis/api/v2/ixos/{endpoint}"
    try:
        r = requests.get(url, headers=HEADERS, verify=False, timeout=5)
        if r.status_code == 200:
            return r.json()
        safe_print(f"❌ GET {endpoint} failed {r.status_code}")
        return []
    except Exception as e:
        safe_print(f"❌ GET Exception {endpoint}: {e}")
        return []

# ======== 建立 Port Map ========
def get_port_map():
    ports = get("ports")
    port_map = {p["id"]: p for p in ports}
    return port_map

# ======== Live Port Stats ========
def get_port_stats(port_map):
    stats = get("portstats")
    lines = []
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    lines.append(f"\n⏱️  {timestamp}")
    lines.append(f"{'ID':<6} {'Port':<8} {'Link':<6} {'Speed':<7} {'Tx Bytes':>12} {'Rx Bytes':>12} {'CRC':>6}")

    for s in sorted(stats, key=lambda x: port_map.get(x.get("parentId"), {}).get("fullyQualifiedPortName", "")):
        pid = s.get("parentId")
        port = port_map.get(pid, {})
        name = port.get("fullyQualifiedPortName", "?")
        link = port.get("linkState", "?")
        speed = f"{port.get('speed', 0)//1000}G"
        tx = s.get("bytesSent", 0)
        rx = s.get("bytesReceived", 0)
        crc = s.get("crcErrors", 0)
        lines.append(f"{pid:<6} {name:<8} {link:<6} {speed:<7} {tx:>12} {rx:>12} {crc:>6}")

    return "\n".join(lines)

# ======== 處理 Panel 傳來的命令 ========
def handle_command(cmd):
    cmd = cmd.strip()
    if not cmd:
        return ""
    return f"[CMD RECEIVED] {cmd}"


# ======== 主監控迴圈（非阻塞 stdin + 每秒刷新） ========
def main():
    safe_print("🚀 Ixia Live Port Monitor Started (REST v2 API)\n")

    port_map = get_port_map()

    while True:
        try:
            # --- 取得即時統計 ---
            live_text = get_port_stats(port_map)
            safe_print(live_text)

            time.sleep(REFRESH_INTERVAL)

        except Exception as e:
            safe_print("[ERROR LOOP]")
            safe_print(traceback.format_exc())
            time.sleep(1)


if __name__ == "__main__":
    main()
