from ixnetwork_restpy import TestPlatform, SessionAssistant
import time
import sys

CHASSIS_IP = "10.89.83.99"
USERNAME = "admin"
PASSWORD = "!Lad12345"

print("🧹 嘗試清除 IxNetwork 上所有舊的 sessions ...")
platform = TestPlatform(CHASSIS_IP, rest_port=443)

# 舊版不支援 Authenticate()
try:
    platform.Authenticate(USERNAME, PASSWORD)
except Exception:
    print("⚠️ 當前版本不支援 Authenticate()，略過驗證")

# 移除所有舊 session
try:
    sessions = platform.Sessions.find()
    if len(sessions) == 0:
        print("✅ 沒有舊的 sessions")
    else:
        for s in sessions:
            try:
                print(f" - 移除舊 session ID={s.Id}")
                s.remove()
            except Exception as e:
                print(f"⚠️ 無法移除 session {s.Id}: {e}")
        time.sleep(2)
        print("✅ 所有舊 sessions 已清除完畢")
except Exception as e:
    print(f"⚠️ 找不到現有 sessions: {e}")

# ===============================================================
# 建立新的 REST Session
# ===============================================================
print(f"🚀 建立新 IxNetwork Session 連線到 {CHASSIS_IP} ...")
session = SessionAssistant(
    IpAddress=CHASSIS_IP,
    RestPort=443,
    UserName=USERNAME,
    Password=PASSWORD,
    ClearConfig=True,
    LogLevel=SessionAssistant.LOGLEVEL_INFO,
)
ixnetwork = session.Ixnetwork
print("✅ 已成功建立 REST session")

# === 加入 chassis ===
chassis = ixnetwork.AvailableHardware.Chassis.add(Hostname=CHASSIS_IP)
card = chassis.Card.find()[0]
ports = card.Port.find()
tx_port, rx_port = ports[4], ports[10]

# === 建立 vport 並綁定實體 port ===
vport_tx = ixnetwork.Vport.add(Name="TxPort")
vport_rx = ixnetwork.Vport.add(Name="RxPort")
vport_tx.ConnectedTo = tx_port.href
vport_rx.ConnectedTo = rx_port.href
time.sleep(3)
print("🔌 vport 綁定完成")

# === 建立 Topology ===
tx_topo = ixnetwork.Topology.add(Name="TxTopo", Vports=[vport_tx])
rx_topo = ixnetwork.Topology.add(Name="RxTopo", Vports=[vport_rx])
tx_dg = tx_topo.DeviceGroup.add(Name="TxDG", Multiplier=1)
rx_dg = rx_topo.DeviceGroup.add(Name="RxDG", Multiplier=1)
tx_dg.Ethernet.add()
rx_dg.Ethernet.add()
print("🧱 已建立 Tx/Rx Topology")

# === 建立 L2 流量 ===
print("📦 建立 Ethernet Traffic Item...")
traffic_item = ixnetwork.Traffic.TrafficItem.add(
    Name="Ethernet_Traffic",
    TrafficType="ethernetVlan"
)
traffic_item.EndpointSet.add(Sources=tx_topo, Destinations=rx_topo)
traffic_item.Generate()
time.sleep(2)
ixnetwork.Traffic.Apply()
time.sleep(2)

print("Traffic Item 狀態：", traffic_item.State)
for stack in traffic_item.ConfigElement.find()[0].Stack.find():
    print("封包 Stack 層級：", stack.DisplayName)
print("✅ Traffic Item 已建立")

# ===============================================================
# 執行封包傳輸
# ===============================================================
print("▶️ 開始傳輸封包 ...")
ixnetwork.Traffic.Apply()
ixnetwork.Traffic.Start()
print("🟢 流量已啟動，等待統計資料中...")
time.sleep(5)

# ===============================================================
# 自動建立 / 抓取 Port Statistics
# ===============================================================
print("📊 嘗試建立 / 抓取 Port Statistics ...")
stats = ixnetwork.Statistics
try:
    view = stats.View.find(Caption="Port Statistics")[0]
except Exception:
    view = stats.View.add(Caption="Port Statistics")
    view.TreeViewNodeName = "Ports"
    view.Type = "layer23TrafficPort"
    view.Visible = True
    view.Active = True
    print("✅ 已手動建立 Port Statistics 視圖")
    time.sleep(3)

# 強制刷新統計
view.Refresh()
time.sleep(3)

# 嘗試多種欄位屬性
columns = []
for attr in ["Data.ColumnCaptions", "Page.ColumnCaptions", "ColumnNames"]:
    try:
        columns = eval(f"view.{attr}")
        if columns:
            break
    except Exception:
        continue

if not columns:
    print("⚠️ 無法取得欄位名稱，請確認版本或統計視圖是否啟用")
    sys.exit(1)

# ===============================================================
# 處理 PageValues 格式的 Port Statistics 資料
# ===============================================================
print("📊 處理 Port Statistics PageValues 資料 ...")

try:
    page_values = view.Data.PageValues
except Exception:
    page_values = []

if not page_values:
    print("⚠️ 找不到 PageValues，請確認流量是否正在執行")
else:
    for entry in page_values:
        # 每個 entry 是一個 [[row_values]] 結構，要取 entry[0][0]
        if isinstance(entry, list) and len(entry) > 0:
            row_values = entry[0]
            row_dict = dict(zip(columns, row_values))
            print(f"Port={row_dict.get('Stat Name')} | "
                  f"Name={row_dict.get('Port Name')} | "
                  f"Speed={row_dict.get('Line Speed')} | "
                  f"TX={row_dict.get('Frames Tx.')} | "
                  f"RX={row_dict.get('Valid Frames Rx.')} | "
                  f"TX Rate={row_dict.get('Tx. Rate (Mbps)')} Mbps | "
                  f"RX Rate={row_dict.get('Rx. Rate (Mbps)')} Mbps | "
                  f"CRC={row_dict.get('CRC Errors')} | "
                  f"pre-FEC BER={row_dict.get('pre FEC Bit Error Ratio')}")


# ===============================================================
# 停止流量
# ===============================================================
print("⏹ 停止傳輸 ...")
ixnetwork.Traffic.Stop()
print("✅ 測試完成")
