import argparse
import sys
import time
import os
import traceback
from netmiko import ConnectHandler

# ======================
# Parse UI port argument
# ======================
parser = argparse.ArgumentParser()
parser.add_argument("--port", type=str, required=True)
args = parser.parse_args()
PORT = args.port

# ======================
# Safe UTF-8 print
# ======================
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

def safe_print(msg):
    try:
        print(msg, flush=True)
    except:
        try:
            print(msg.encode("utf-8", "replace").decode("utf-8"), flush=True)
        except:
            pass

# ======================
# Connect Arista
# ======================
def connect_arista(ip, user, pwd):
    dev = {
        'device_type': 'arista_eos',
        'ip': ip,
        'username': user,
        'password': pwd,
    }
    safe_print(f"🔌 Connecting to {ip} ...")
    conn = ConnectHandler(**dev)
    conn.enable()
    conn.global_cmd_verify = False
    conn.read_timeout = 1
    conn.send_command("terminal length 0")
    safe_print("✅ Connected successfully!\n")
    return conn

# ======================
# FAST GETTER
# ======================
def fast_cmd(conn, cmd):
    """Optimized for speed"""
    return conn.send_command(
        cmd,
        expect_string=r"#",
        delay_factor=0.05,
        max_loops=3
    )

# ======================
# MAIN FAST MONITOR
# ======================
def fast_monitor(port, interval=0.2):
    conn = connect_arista("10.89.83.55", "admin", "Intel@123")

    safe_print(f"🚀 Fast Monitor Started (Ethernet {port}/1)\n")

    # SFP info 只在第一次抓（非常慢，不要每次抓）
    sfp_info = fast_cmd(conn, f"show interfaces ethernet {port}/1 transceiver")  

    while True:
        try:
            info = fast_cmd(conn, f"show interfaces ethernet {port}/1")
            # 1) Link status (very fast)
            #link_info = fast_cmd(conn, f"show interfaces ethernet {port}/1 status")

            # 2) Rates (fast)
            #rate_info = fast_cmd(conn, f"show interfaces ethernet {port}/1 counters rates")

            # 3) Error counters (medium)
            #error_info = fast_cmd(conn, f"show interfaces ethernet {port}/1 counters")

            # ========== OUTPUT ==========
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            safe_print(f"⏱  {timestamp}   |   Ethernet {port}/1")
            safe_print(info)
            
            #safe_print("\n🔵 Link Status:")
            #safe_print(link_info)

            #safe_print("\n📊 Rates:")
            #safe_print(rate_info)

            #safe_print("\n⚠️  Error Counters:")
            #safe_print(error_info)

            #safe_print("\n💡 SFP Info (cached):")
            #safe_print(sfp_info)

            time.sleep(interval)

        except Exception:
            safe_print("\n[ERROR]")
            safe_print(traceback.format_exc())
            time.sleep(1)

# ======================
# ENTRY
# ======================
if __name__ == "__main__":
    fast_monitor(PORT)
