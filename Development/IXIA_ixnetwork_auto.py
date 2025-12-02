import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from ixnetwork_restpy import TestPlatform, SessionAssistant
from ixnetwork_restpy.errors import UnauthorizedError
import time
import threading
import os
import sys
import random


# === 全域設定 ===
CHASSIS_IP = "10.89.83.99"
USERNAME = "admin"
PASSWORD = "!Lad12345"
tx_port_idx = 4
rx_port_idx = 10
session = None
ixnetwork = None


# ==============================================================
# 登入 TestPlatform（支援帳密或 API Key）
# ==============================================================
def _login_testplatform():
    api_key = os.getenv("IXN_API_KEY", "").strip()
    last_error = None
    platform = TestPlatform(CHASSIS_IP, rest_port=443, platform="linux", verify_cert=False)

    try:
        platform.Authenticate(USERNAME, PASSWORD)
        print("🔐 Login successful")
        return platform
    except Exception as e:
        print(f"⚠️ Login failed：{e}")
        last_error = e

    if api_key:
        try:
            platform = TestPlatform(
                CHASSIS_IP, rest_port=443, platform="linux", verify_cert=False, apiKey=api_key
            )
            _ = platform.Sessions.find()
            print("🔐 Login successful by API key")
            return platform
        except Exception as e:
            print(f"⚠️ API Key login failed：{e}")
            last_error = e

    raise UnauthorizedError(f"❌ Can't login TestPlatform，failed：{last_error}")


# ==============================================================
# 1️⃣ 清空舊的 REST Sessions
# ==============================================================
def clear_old_sessions():
    print("🧹 Try to remove all REST sessions ...")
    try:
        platform = _login_testplatform()
        sessions = platform.Sessions.find()
        if not sessions:
            print("✅ No any sessions")
        else:
            for s in sessions:
                try:
                    print(f" - Remove session ID={s.Id}")
                    s.remove()
                except Exception as e:
                    print(f"⚠️ Can't remove session {s.Id}: {e}")
            time.sleep(2)
            print("✅ All sessions are removed.")
    except Exception as e:
        print(f"❌ Remove failed：{e}")


# ==============================================================
# 2️⃣ 建立新的 Session（含 vport/topology/traffic）
# ==============================================================
def create_new_session():
    global session, ixnetwork
    print(f"🚀 建立新 IxNetwork Session 連線到 {CHASSIS_IP} ...")
    try:
        session = SessionAssistant(
            IpAddress=CHASSIS_IP,
            RestPort=443,
            UserName=USERNAME,
            Password=PASSWORD,
            ClearConfig=True,
            LogLevel=SessionAssistant.LOGLEVEL_INFO,
        )
        ixnetwork = session.Ixnetwork
        print("✅ Success to creat new REST session")
        bind_ports()
    except Exception as e:
        print(f"❌ 建立新 Session 失敗：{e}")


# ==============================================================
# 3️⃣ 使用舊的 Session（選擇接管）
# ==============================================================
def use_existing_session():
    global session, ixnetwork
    print("🔎 Try to detect available sessions ...")

    try:
        platform = _login_testplatform()
        sessions = platform.Sessions.find()
        if not sessions:
            print("⚠️ No available session，please create new session（Action 2）")
            return

        print("\n📜 Available sessions：")
        for s in sessions:
            print(f"  Session ID={s.Id} | State={s.State} | User={s.UserName}")

        choice = input("\nPlease select session ID：").strip()
        match = [s for s in sessions if str(s.Id) == choice]
        if not match:
            print("❌ Not found session ID")
            return

        sel = match[0]
        print(f"🔗 Try to take over Session ID={choice} ...")

        ixnetwork = sel.Ixnetwork
        print(f"✅ Success to take over Session ID={choice}")

        vports = ixnetwork.Vport.find()
        if vports:
            print("🔍 Current vport setting：")
            for vp in vports:
                print(f"  - {vp.Name} → {vp.ConnectedTo}")
        else:
            print("⚠️ No vport setting")

    except Exception as e:
        print(f"❌ Take over Session failed：{e}")



# ==============================================================
# 綁定 vport / 建立 Topology / Traffic
# ==============================================================
def bind_ports():
    global ixnetwork, tx_port_idx, rx_port_idx
    print("🔌 Re-setting vport ...")

    try:
        old_vports = ixnetwork.Vport.find()
        if old_vports:
            print(f"🧹 Remove {len(old_vports)}  vport ...")
            old_vports.remove()
        old_traffic = ixnetwork.Traffic.TrafficItem.find()
        if old_traffic:
            print(f"🧹 Remove {len(old_traffic)} TrafficItem ...")
            old_traffic.remove()
        time.sleep(1)
    except Exception as e:
        print(f"⚠️ Remove items failed：{e}")

    chassis = ixnetwork.AvailableHardware.Chassis.add(Hostname=CHASSIS_IP)
    card = chassis.Card.find()[0]
    ports = card.Port.find()
    tx_port = ports[tx_port_idx]
    rx_port = ports[rx_port_idx]

    vport_tx = ixnetwork.Vport.add(Name="TxPort")
    vport_rx = ixnetwork.Vport.add(Name="RxPort")
    vport_tx.ConnectedTo = tx_port.href
    vport_rx.ConnectedTo = rx_port.href
    time.sleep(2)

    print(f"✅ vport setting successful：Tx={tx_port_idx}, Rx={rx_port_idx}")

    tx_topo = ixnetwork.Topology.add(Name="TxTopo", Vports=[vport_tx])
    rx_topo = ixnetwork.Topology.add(Name="RxTopo", Vports=[vport_rx])
    tx_topo.DeviceGroup.add(Name="TxDG", Multiplier=1).Ethernet.add()
    rx_topo.DeviceGroup.add(Name="RxDG", Multiplier=1).Ethernet.add()

    traffic_item = ixnetwork.Traffic.TrafficItem.add(
        Name="Ethernet_Traffic", TrafficType="ethernetVlan"
    )
    traffic_item.EndpointSet.add(Sources=tx_topo, Destinations=rx_topo)
    traffic_item.Generate()
    ixnetwork.Traffic.Apply()
    print("✅ Success to create Traffic Item")


# ==============================================================
# 4️⃣ start traffic
# ==============================================================
def start_traffic():
    print("▶️ Start transmit ...")
    ixnetwork.Traffic.Apply()
    ixnetwork.Traffic.Start()


# ==============================================================
# 5️⃣ stop traffic
# ==============================================================
def stop_traffic():
    print("⏹ Stop transmit ...")
    ixnetwork.Traffic.Stop()


# ==============================================================
# 6️⃣ 清除統計資料
# ==============================================================
def clear_packet_counters():
    print("🧹 Clear counters ...")
    ixnetwork.ClearStats()
    time.sleep(1)
    print("✅ Cleared")


# ==============================================================
# 8️⃣ Show TrafficItem MAC（你的裝置的 API 是 read-only 00:00）
# ==============================================================
def get_traffic_mac():
    global ixnetwork
    print("\n📦 Current Traffic Header MAC (latest editable header):")

    try:
        ti = ixnetwork.Traffic.TrafficItem.find()[0]
        ce = ti.ConfigElement.find()[0]

        # 找最新 Ethernet Header（最後一個）
        eth_list = ce.Stack.find(StackTypeId="ethernet")
        if not eth_list or len(eth_list) == 0:
            print("❌ No Ethernet header found")
            return

        eth = eth_list[-1]

        # 找 Source/Destination Field
        sa_field = eth.Field.find(DisplayName="Source MAC Address")[0]
        da_field = eth.Field.find(DisplayName="Destination MAC Address")[0]

        # ⭐ 正確讀取（你的 chassis 使用 FormattedFieldValue）
        sa = sa_field.FormattedFieldValue
        da = da_field.FormattedFieldValue

        print(f"   SA = {sa}")
        print(f"   DA = {da}")
        print("------------------------------------------------")

    except Exception as e:
        print(f"❌ Cannot read: {e}")



# ==============================================================
# 🔧 重建 Ethernet Header（讓 SA/DA 可寫入）
# ==============================================================
def reset_ethernet_header():
    global ixnetwork
    print("\n🔧 Adding new editable Ethernet Header (AppendProtocol)...\n")

    try:
        ti = ixnetwork.Traffic.TrafficItem.find()[0]
        ce = ti.ConfigElement.find()[0]

        # ⭐ AresONE / FPGA ONLY working method
        ce.Stack.AppendProtocol("ethernet")

        ixnetwork.Traffic.Apply()

        print("✅ New Ethernet Header added (editable SA/DA enabled)\n")

    except Exception as e:
        print("❌ Failed to rebuild:", e)




# ==============================================================
# 🔥 Auto Sync MAC (Tx <-> Rx) — 可寫入模式（FieldValue）
# ==============================================================
def random_mac():
    return "02:" + ":".join(f"{random.randint(0,255):02x}" for _ in range(5))

def auto_sync_mac():
    print("\n🔄 Auto Sync MAC (Tx ↔ Rx via FieldValue)...\n")

    try:
        ti = ixnetwork.Traffic.TrafficItem.find()[0]
        ce = ti.ConfigElement.find()[0]
        eth = ce.Stack.find(StackTypeId="ethernet")[0]

        sa_field = eth.Field.find(DisplayName="Source MAC Address")[0]
        da_field = eth.Field.find(DisplayName="Destination MAC Address")[0]

        old_sa = sa_field.FieldValue
        old_da = da_field.FieldValue

        # default 00:00:00:00:00:00 → replace
        if old_sa == "00:00:00:00:00:00":
            old_sa = random_mac()
        if old_da == "00:00:00:00:00:00":
            old_da = random_mac()

        new_sa = old_da
        new_da = old_sa

        sa_field.update(FieldValue=new_sa)
        da_field.update(FieldValue=new_da)

        ixnetwork.Traffic.Apply()

        print(f"👉 New SA = {new_sa}")
        print(f"👉 New DA = {new_da}")
        print("\n✅ MAC Sync Completed\n")

    except Exception as e:
        print("❌ Failed:", e)


# ==============================================================
# Debug Field API
# ==============================================================
def debug_fields():
    global ixnetwork
    print("\n🔍 Debugging all fields in latest Ethernet header...\n")

    ti = ixnetwork.Traffic.TrafficItem.find()[0]
    ce = ti.ConfigElement.find()[0]

    eth_list = ce.Stack.find(StackTypeId="ethernet")
    eth = eth_list[-1]  # 最新 header

    # 列出所有 Field 元資料
    print("📌 All Fields:")
    fields = eth.Field.find()
    for f in fields:
        print("\n--------------------------------------")
        print("DisplayName:", f.DisplayName)
        print("Name:", f.Name)

        # 列出所有 attrs
        try:
            attrs = f.get_attributes()
            print("\nAttributes:")
            for k, v in attrs.items():
                print(f"  {k} = {v}")
        except:
            print("  (cannot get attributes)")

        # 列出所有 methods
        print("\nMethods:")
        for m in dir(f):
            if not m.startswith("_"):
                print("  ", m)



# ==============================================================
# 主選單
# ==============================================================
while True:
    print("\n==================== Menu ====================")
    print("1. Remove all REST session")
    print("2. Create new REST session")
    print("3. Use existing session")
    print("4. Start transmit")
    print("5. Stop transmit")
    print("6. Clear counters")
    print("7. Change Tx/Rx port")
    print("8. Show Traffic MAC")
    print("9. 🔧 Rebuild Ethernet Header")
    print("10. 🔄 Auto Sync MAC (Tx <-> Rx)")
    print("11. Debug Field API")
    print("0. Exit")
    print("===============================================")

    choice = input("Please select action：").strip()

    if choice == "1":
        clear_old_sessions()
    elif choice == "2":
        create_new_session()
    elif choice == "3":
        use_existing_session()
    elif choice == "4":
        start_traffic()
    elif choice == "5":
        stop_traffic()
    elif choice == "6":
        clear_packet_counters()
    elif choice == "7":
        change_ports()
    elif choice == "8":
        get_traffic_mac()
    elif choice == "9":
        reset_ethernet_header()
    elif choice == "10":
        auto_sync_mac()
    elif choice == "11":
        debug_fields()
    elif choice == "0":
        print("👋 Exit")
        sys.exit(0)
    else:
        print("❌ Invalid input.")
