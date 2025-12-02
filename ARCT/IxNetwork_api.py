import sys
import time
import os
from ixnetwork_restpy import TestPlatform, SessionAssistant
from ixnetwork_restpy.errors import UnauthorizedError

# ==============================
# UTF-8 Safe Output
# ==============================
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

def println(msg=""):
    print(msg, flush=True)

# ==============================
# Global Settings
# ==============================
CHASSIS_IP = "10.89.83.99"
USERNAME = "admin"
PASSWORD = "!Lad12345"

session = None
ixnetwork = None

# ==============================================================
def _login_testplatform():
    api_key = os.getenv("IXN_API_KEY", "").strip()
    platform = TestPlatform(CHASSIS_IP, rest_port=443, platform="linux", verify_cert=False)

    try:
        platform.Authenticate(USERNAME, PASSWORD)
        println("🔐 Login successful")
        return platform
    except Exception as e:
        println(f"⚠️ Login failed：{e}")

    if api_key:
        try:
            platform = TestPlatform(
                CHASSIS_IP, rest_port=443, platform="linux",                verify_cert=False,
                apiKey=api_key
            )
            _ = platform.Sessions.find()
            println("🔐 Login successful by API key")
            return platform
        except Exception as e:
            println(f"⚠️ API Key login failed：{e}")

    raise UnauthorizedError("❌ Can't login TestPlatform")


# ==============================================================
def show_control_session():
    println("🧩 Program-Controlled Session Info:")

    global session, ixnetwork

    if session is None or ixnetwork is None:
        println("❌ No active session in this program.")
        println("Please create new session or use existing session first.")
        return

    try:
        # SessionAssistant has .Session
        sess = session.Session
        println(f"Session ID     : {sess.Id}")
        '''println(f"User           : {sess.UserName}")
        println(f"State          : {sess.State}")
        println(f"Application    : {sess.ApplicationType}")
        println(f"Session href   : {sess.href}")

        # IxNetwork object
        println(f"IxNetwork href : {ixnetwork.href}")'''

        # Show vPorts
        vports = ixnetwork.Vport.find()
        println(f"vPorts         : {[vp.Name for vp in vports]}")

        # Show Topology count
        topos = ixnetwork.Topology.find()
        println(f"Topology count : {len(topos)}")

        # Show TrafficItem count
        ti = ixnetwork.Traffic.TrafficItem.find()
        println(f"Traffic Items  : {len(ti)}")

        # State detail
        try:
            ixn_state = ixnetwork.Globals.Topology.State
            println(f"IxNetwork State: {ixn_state}")
        except:
            pass

    except Exception as e:
        println(f"❌ Failed to retrieve program-controlled session: {e}")
# ==============================================================
def clear_old_sessions():
    println("🧹 Try to remove all REST sessions ...")
    try:
        platform = _login_testplatform()
        sessions = platform.Sessions.find()
        if not sessions:
            println("✅ No any sessions")
        else:
            for s in sessions:
                try:
                    println(f" - Remove session ID={s.Id}")
                    s.remove()
                except Exception as e:
                    println(f"⚠️ Can't remove session {s.Id}: {e}")
            time.sleep(1)
            println("✅ All sessions removed")
    except Exception as e:
        println(f"❌ Remove failed：{e}")
# ==============================================================
def create_new_session():
    global session, ixnetwork
    println("🚀 Create new IxNetwork Session...")
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
        println("✅ Success create new REST session")
        bind_ports()
    except Exception as e:
        println(f"❌ Fail to create Session：{e}")
# ==============================================================
def use_existing_session():
    global session, ixnetwork
    println("🔎 Listing available sessions ...")

    try:
        platform = _login_testplatform()
        sessions = platform.Sessions.find()
        if not sessions:
            println("⚠️ No available session")
            return

        for s in sessions:
            println(f"  Session ID={s.Id} | State={s.State} | User={s.UserName}")

        println("Please select session ID：")
        choice = sys.stdin.readline().strip()

        match = [s for s in sessions if str(s.Id) == choice]
        if not match:
            println("❌ Not found session ID")
            return

        sel = match[0]
        println(f"🔗 Take over Session {choice}")

        # ⭐⭐ 關鍵點：直接 attach 到同一個 REST Session ⭐⭐
        session = SessionAssistant(
            IpAddress=CHASSIS_IP,
            RestPort=443,
            UserName=USERNAME,
            Password=PASSWORD,
            SessionId=sel.Id,             # <--- 加這個
            ClearConfig=False,            # 不要清除設定
            LogLevel=SessionAssistant.LOGLEVEL_INFO,
        )

        ixnetwork = session.Ixnetwork
        println("✅ Session attached successfully")

    except Exception as e:
        println(f"❌ Take over failed：{e}")

# ==============================================================
def bind_ports():
    global ixnetwork, tx_port_idx, rx_port_idx

    try:
        old_vports = ixnetwork.Vport.find()
        if old_vports:
            old_vports.remove()
    except:
        pass

    time.sleep(0.3)

    chassis = ixnetwork.AvailableHardware.Chassis.add(Hostname=CHASSIS_IP)
    card = chassis.Card.find()[0]
    ports = card.Port.find()
    
    used_ports = []
    for i, port in enumerate(ports):
        if port.Owner and TARGET_OWNER_KEYWORD in port.Owner:
            used_ports.append(i)

    if used_ports:
        used_str = ", ".join([f"Port[{i}]" for i in used_ports])
        println(f"🟡 Current Using Ports: {used_str}")
    else:
        println("🟢 No port is currently used.")

    # -------------------------
    # 可用的 Port
    # -------------------------
    println("\nAvailable Ports:")
    available_ports = []
    for i, port in enumerate(ports):
        if port.IsAvailable and i not in used_ports:
            available_ports.append(i)
            println(f"Port[{i}] → {port.Description}")
            println(f"   LinkUp: {port.IsLinkUp}")
            println("")

    if not available_ports:
        println("⚠️ No available port")
        return
    println("Select Tx port:")
    tx_port_idx = int(sys.stdin.readline().strip())
    
    println("Select Rx port:")
    rx_port_idx = int(sys.stdin.readline().strip())

    tx = ports[tx_port_idx]
    rx = ports[rx_port_idx]

    vtx = ixnetwork.Vport.add(Name="TxPort")
    vrx = ixnetwork.Vport.add(Name="RxPort")

    vtx.ConnectedTo = tx.href
    vrx.ConnectedTo = rx.href

    println(f"🔌 Bound Tx={tx_port_idx}, Rx={rx_port_idx}")

    time.sleep(0.3)

    tx_topo = ixnetwork.Topology.add(Name="TxTopo", Vports=[vtx])
    rx_topo = ixnetwork.Topology.add(Name="RxTopo", Vports=[vrx])

    tx_topo.DeviceGroup.add(Multiplier=1).Ethernet.add()
    rx_topo.DeviceGroup.add(Multiplier=1).Ethernet.add()

    '''traffic = ixnetwork.Traffic.TrafficItem.add(
        Name="Traffic1",
        TrafficType="ethernetVlan"
    )
    traffic.EndpointSet.add(
        Sources=tx_topo,
        Destinations=rx_topo
    )
    traffic.Generate()
    
    traffic2 = ixnetwork.Traffic.TrafficItem.add(
        Name="Traffic2",
        TrafficType="ethernetVlan"
    )
    traffic2.EndpointSet.add(
        Sources=rx_topo,
        Destinations=tx_topo
    )
    traffic2.Generate()
    ixnetwork.Traffic.Apply()'''

    println("✔ Configured topology")
# ==============================================================
def start_traffic():
    println("▶ Start Traffic ...")
    ixnetwork.Traffic.Apply()
    ixnetwork.Traffic.Start()
    println("✔ Traffic started")


def stop_traffic():
    println("⏹ Stop Traffic ...")
    ixnetwork.Traffic.Stop()
    println("✔ Traffic stopped")


def clear_counters():
    println("🧹 Clear counters ...")
    ixnetwork.ClearStats()
    println("✔ Cleared")
# ==============================================================
def change_ports():
    global ixnetwork, tx_port_idx, rx_port_idx

    if ixnetwork is None:
        println("❌ No available Session")
        return

    try:
        chassis = ixnetwork.AvailableHardware.Chassis.find()[0]
        card = chassis.Card.find()[0]
        ports = card.Port.find()
        TARGET_OWNER_KEYWORD = "IxNetwork/ixnetworkweb/admin"

        println("\n================ PORT STATUS ================")

        # -------------------------
        # 使用中的 Port
        # -------------------------
        used_ports = []
        for i, port in enumerate(ports):
            if port.Owner and TARGET_OWNER_KEYWORD in port.Owner:
                used_ports.append(i)

        if used_ports:
            used_str = ", ".join([f"Port[{i}]" for i in used_ports])
            println(f"🟡 Current Using Ports: {used_str}")
        else:
            println("🟢 No port is currently used.")

        # -------------------------
        # 可用的 Port
        # -------------------------
        println("\nAvailable Ports:")
        available_ports = []
        for i, port in enumerate(ports):
            if port.IsAvailable and i not in used_ports:
                available_ports.append(i)
                println(f"Port[{i}] → {port.Description}")
                println(f"   LinkUp: {port.IsLinkUp}")
                println("")

        if not available_ports:
            println("⚠️ No available port")
            return

        # -------------------------
        # 選 Tx Port
        # -------------------------
        println("Select new Tx port index:")
        tx_port_idx = int(sys.stdin.readline().strip())

        # -------------------------
        # 選 Rx Port
        # -------------------------
        println("Select new Rx port index:")
        rx_port_idx = int(sys.stdin.readline().strip())

        tx_port = ports[tx_port_idx]
        rx_port = ports[rx_port_idx]

        println(f"\n🔌 Selected New Tx: {tx_port.Description} (PortId {tx_port.PortId})")
        println(f"🔌 Selected New Rx: {rx_port.Description} (PortId {rx_port.PortId})")

        # -------------------------
        # 重新綁定到 vports
        # -------------------------
        vports = ixnetwork.Vport.find()
        if len(vports) < 2:
            println("❌ No available vport")
            return

        vport_tx = vports[0]
        vport_rx = vports[1]

        vport_tx.ConnectedTo = tx_port.href
        vport_rx.ConnectedTo = rx_port.href

        println("\n✔ Port binding updated:")
        println(f"   {vport_tx.Name} → {vport_tx.ConnectedTo}")
        println(f"   {vport_rx.Name} → {vport_rx.ConnectedTo}")

    except Exception as e:
        println(f"❌ Error during changing ports: {e}")
# ==============================================================
def set_ethertype(hex_value):
    println(f"🛠 Set Ethernet-Type = 0x{hex_value}")

    try:
        for name in ["Traffic1", "Traffic2"]:
            traffic = ixnetwork.Traffic.TrafficItem.find(Name=name)
            if not traffic:
                println(f"⚠️ {name} Not found")
                continue

            cfg = traffic.ConfigElement.find()[0]

            # 找 Ethernet Stack 名稱 (自動偵測)
            eth_stack = None
            for s in cfg.Stack.find():
                if "Ethernet" in s.DisplayName:
                    eth_stack = s
                    break

            if not eth_stack:
                println(f"❌ {name} Not found Ethernet Stack")
                continue

            # 找 Ethertype 欄位
            field = eth_stack.Field.find(DisplayName="Ethernet-Type")
            if not field:
                println(f"❌ {name} Not found Ethernet-Type value")
                continue

            # 必須先關閉 AUTO，否則 value 永遠不會生效
            field.Auto = False

            # 改為 Single Value
            field.ValueType = "singleValue"

            # 設定值
            field.SingleValue = hex_value

            traffic.Generate()

        ixnetwork.Traffic.Apply()
        println(f"✔ Ethernet-Type updated → 0x{hex_value}")

    except Exception as e:
        println(f"❌ Error to set Ethertype：{e}")
# ==============================================================
def set_frame_size(fixed=None, min_size=None, max_size=None):
    try:
        for name in ["Traffic1", "Traffic2"]:
            traffic = ixnetwork.Traffic.TrafficItem.find(Name=name)
            if not traffic:
                println(f"⚠️ {name} not found，skipped")
                continue

            cfg = traffic.ConfigElement.find()[0]

            if fixed:
                cfg.FrameSize.Type = "fixed"
                cfg.FrameSize.FixedSize = fixed
                println(f"{name} → Fixed Size = {fixed}")

            elif min_size and max_size:
                cfg.FrameSize.Type = "increment"
                cfg.FrameSize.IncrementFrom = min_size
                cfg.FrameSize.IncrementTo = max_size
                cfg.FrameSize.IncrementStep = 1
                println(f"{name} → Random {min_size}-{max_size}")

            traffic.Generate()

        ixnetwork.Traffic.Apply()
        println("✔ Frame size updated")

    except Exception as e:
        println(f"❌ Error to set frame size：{e}")
# ==============================================================
def show_traffic_items():
    println("📦 Traffic Items List:")
    try:
        items = ixnetwork.Traffic.TrafficItem.find()

        if len(items) == 0:
            println("⚠️ No Traffic Item found.")
            return

        for i, ti in enumerate(items):
            println(f"\n[{i}] Name       : {ti.Name}")
            println(f"    Enabled    : {ti.Enabled}")
            println(f"    TrafficType: {ti.TrafficType}")
            println(f"    State      : {ti.State}")

            cfg = ti.ConfigElement.find()[0]

            # ------------------------------
            # Frame Size
            # ------------------------------
            fs = cfg.FrameSize
            println("    FrameSize:")
            println(f"       Type      : {fs.Type}")

            if fs.Type == "fixed":
                println(f"       FixedSize : {fs.FixedSize}")

            elif fs.Type == "increment":
                println(f"       From      : {fs.IncrementFrom}")
                println(f"       To        : {fs.IncrementTo}")
                println(f"       Step      : {fs.IncrementStep}")

            elif fs.Type == "random":
                println(f"       Min       : {fs.RandomMin}")
                println(f"       Max       : {fs.RandomMax}")

            # ------------------------------
            # Ethernet-Type
            # ------------------------------
            ethertype_value = None
            try:
                # 找 Ethernet Stack
                eth_stack = None
                for s in cfg.Stack.find():
                    if "Ethernet" in s.DisplayName:
                        eth_stack = s
                        break

                if eth_stack:
                    field = eth_stack.Field.find(DisplayName="Ethernet-Type")
                    if field:
                        if field.Auto:
                            ethertype_value = f"<Auto> {field.SingleValue}"
                        else:
                            ethertype_value = field.SingleValue

            except Exception as e:
                ethertype_value = f"ERROR: {e}"

            println(f"    Ethernet-Type: {ethertype_value}")

            # ------------------------------
            # Endpoints
            # ------------------------------
            eps = ti.EndpointSet.find()
            if not eps:
                println("    No endpoints")
                continue

            for ep in eps:
                src_list = []
                dst_list = []

                for o in ep.Sources:
                    src_list.append(o.href if hasattr(o, "href") else str(o))

                for o in ep.Destinations:
                    dst_list.append(o.href if hasattr(o, "href") else str(o))

                println(f"    Src(s): {src_list}")
                println(f"    Dst(s): {dst_list}")

    except Exception as e:
        println(f"❌ Failed to list traffic items: {e}")

# ==============================================================
def add_traffic_item():
    try:
        # ---- 找出所有 topologies ----
        topos = ixnetwork.Topology.find()

        if len(topos) == 0:
            println("❌ No topology found. Please bind ports first.")
            return

        println("📡 Available Topology：")
        for i, topo in enumerate(topos):
            println(f"  [{i}] {topo.Name}   (Ports={len(topo.Vports)})")

        # ----------------------------------------
        #   選擇 Tx Topology
        # ----------------------------------------
        println("\n Source(Tx) Topology：")
        try:
            tx_idx = int(sys.stdin.readline().strip())
        except:
            println("❌ Invalid input")
            return

        if tx_idx < 0 or tx_idx >= len(topos):
            println("❌ Topology out of range")
            return

        tx_topo = topos[tx_idx]
        println(f"➡️  Select TxTopo：{tx_topo.Name}")

        # ----------------------------------------
        #   選擇 Rx Topology
        # ----------------------------------------
        println("\nDestination(Rx) Topology：")
        try:
            rx_idx = int(sys.stdin.readline().strip())
        except:
            println("❌ Invalid input")
            return

        if rx_idx < 0 or rx_idx >= len(topos):
            println("❌ Topology out of range")
            return

        rx_topo = topos[rx_idx]
        println(f"⬅️  Select RxTopo：{rx_topo.Name}")

        # ----------------------------------------
        #   輸入 Traffic Item 名稱
        # ----------------------------------------
        println("\nNew Traffic Item name (valid name: 1) Traffic1 2) Traffic2：")
        name = sys.stdin.readline().strip()

        if name == "1":
            name = "Traffic1"
        if name == "2":
            name = "Traffic2"
        elif name == "":
            println("❌ No blank")
            return

        println(f"📦 Adding Traffic Item: {name}")

        # ----------------------------------------
        #   建立 Traffic Item
        # ----------------------------------------
        ti = ixnetwork.Traffic.TrafficItem.add(
            Name=name,
            TrafficType="ethernetVlan",
            Enabled=True
        )

        ti.EndpointSet.add(
            Sources=tx_topo,
            Destinations=rx_topo
        )

        ti.Generate()
        ixnetwork.Traffic.Apply()

        println(f"✔ Traffic Item '{name}' generated！")

    except Exception as e:
        println(f"❌ error：{e}")
        
def normalize_mac(mac):
    mac = mac.strip().lower().replace(":", "").replace("-", "")
    if len(mac) != 12:
        raise ValueError("MAC must be 12 hex digits")
    return ":".join(mac[i:i+2] for i in range(0, 12, 2))


def add_raw_traffic_item():
    try:
        vports = ixnetwork.Vport.find()

        if len(vports) < 2:
            println("❌ Need at least 2 vports bound.")
            return

        # --------------------------------------------
        # ⭐ Step 1: 確保 vport.protocols 有 default L2
        # --------------------------------------------
        for vp in vports:
            if len(vp.Protocols.find()) == 0:
                vp.Protocols.add()
                time.sleep(0.2)

        # --------------------------------------------
        # 顯示 vport 給使用者選
        # --------------------------------------------
        println("📡 Vports:")
        for i, vp in enumerate(vports):
            println(f"  [{i}] {vp.Name}")

        println("Select Tx index:")
        tx = vports[int(sys.stdin.readline().strip())]

        println("Select Rx index:")
        rx = vports[int(sys.stdin.readline().strip())]

        # RAW endpoint
        tx_ep = tx.Protocols.find()
        rx_ep = rx.Protocols.find()

        # --------------------------------------------
        # TrafficItem Name
        # --------------------------------------------
        println("Traffic Name (1=Traffic1, 2=Traffic2):")
        name = "Traffic1" if sys.stdin.readline().strip() == "1" else "Traffic2"

        println(f"📦 Adding RAW TrafficItem: {name}")

        # --------------------------------------------
        # User input options
        # --------------------------------------------
        
        # --- SA
        println("Enter Source MAC (default: 00:22:33:44:55:66):")
        sa_in = sys.stdin.readline().strip()
        if sa_in == "":
            sa = "00:22:33:44:55:66"
        else:
            sa = normalize_mac(sa_in)
        # --- DA
        println("Enter Destination MAC (default: 00:11:22:33:44:55):")
        da_in = sys.stdin.readline().strip()
        if da_in == "":
            da = "00:11:22:33:44:55"
        else:
            da = normalize_mac(da_in)

        # --- Frame Size
        println("Enter FrameSize in bytes (default: 128):")
        fs = sys.stdin.readline().strip()
        if fs == "":
            fs = 128
        else:
            fs = int(fs)

        # --- FrameRate (% line rate)
        println("Enter FrameRate in % line-rate (default: 100):")
        fr = sys.stdin.readline().strip()
        if fr == "":
            fr = 100
        else:
            fr = int(fr)

        # --------------------------------------------
        # Create Traffic Item
        # --------------------------------------------
        ti = ixnetwork.Traffic.TrafficItem.add(
            Name=name,
            TrafficType="raw"
        )

        # Endpoint
        ti.EndpointSet.add(
            Sources=tx_ep,
            Destinations=rx_ep
        )

        # Generate CE
        ti.Generate()

        cfg = ti.ConfigElement.find()[0]
        eth = cfg.Stack.find(StackTypeId="ethernet")

        # --------------------------------------------
        # Apply user settings
        # --------------------------------------------
        eth.Field.find(DisplayName="Destination MAC").SingleValue = da
        eth.Field.find(DisplayName="Source MAC").SingleValue = sa

        cfg.FrameSize.FixedSize = fs
        cfg.FrameRate.update(Type="percentLineRate", Rate=fr)
        cfg.TransmissionControl.update(Type="continuous")

        # --------------------------------------------
        # Apply traffic
        # --------------------------------------------
        ixnetwork.Traffic.Apply()
        println(f"✔ RAW TrafficItem '{name}' created!")
        println(f"   DA={da}, SA={sa}, FrameSize={fs}, FrameRate={fr}%")

    except Exception as e:
        println(f"❌ error：{e}")

        
# ==============================================================
def delete_traffic_items():
    try:
        items = ixnetwork.Traffic.TrafficItem.find()

        if len(items) == 0:
            println("⚠️ No Traffic Items to delete.")
            return

        println("📦 Existing Traffic Items:")
        for i, ti in enumerate(items):
            println(f"  [{i}] {ti.Name} (Enabled={ti.Enabled}, Type={ti.TrafficType})")

        println("\nRemove which Traffic Item?")
        println("Select item or use 'a' to delete all：")
        choice = sys.stdin.readline().strip()

        # ---- 刪除全部 ----
        if choice.lower() == "a":
            println("🗑️ Deleting ALL traffic items...")
            for ti in items:
                name = ti.Name
                println(f" - Removing {name}")
                ti.remove()
            ixnetwork.Traffic.Apply()
            println("✔ All Traffic Items removed.")
            return

        # ---- 刪除單一 ----
        try:
            idx = int(choice)
        except:
            println("❌ Invalid input.")
            return

        if idx < 0 or idx >= len(items):
            println("❌ Index out of range.")
            return

        ti = items[idx]
        name = ti.Name
        println(f"🗑️ Removing Traffic Item: {name}")
        ti.remove()
        ixnetwork.Traffic.Apply()

        println(f"✔ Traffic Item '{name}' removed.")

    except Exception as e:
        println(f"❌ Failed to delete traffic items: {e}")
# ==============================================================
while True:
    show_control_session()
    println("\n==================== Menu ====================")
    println("1. Remove all REST session")
    println("2. Create new REST session")
    println("3. Use existing session")
    println("4. Start transmit")
    println("5. Stop transmit")
    println("6. Clear counters")
    println("7. Change Tx/Rx port")
    println("8. Set Ethernet-Type")
    println("9. Set Frame Size")
    println("10. Set traffic items")
    println("===============================================")
    print("Select action：", flush=True)

    choice = sys.stdin.readline().strip()

    if choice == "1":
        clear_old_sessions()
    elif choice == "2":
        create_new_session()
    elif choice == "3":
        use_existing_session()
    elif choice == "4":
        start_traffic()
        time.sleep(2)
    elif choice == "5":
        stop_traffic()
        time.sleep(2)
    elif choice == "6":
        clear_counters()
    elif choice == "7":
        change_ports()
    elif choice == "8":
        show_traffic_items()
        println("\nSet Ethernet-Type:(ex: ffff / 0800) or '0' to Cancel：")
        value = sys.stdin.readline().strip()
        if value =="0":
            print("Action canceled.")
        else:
            set_ethertype(value)
    elif choice == "9":
        show_traffic_items()
        println("\nSet Frame Size：1) fixed 2) random 0)Cancel")
        mode = sys.stdin.readline().strip()
        if mode == "1":
            println("Fixed frame size：")
            size = int(sys.stdin.readline().strip())
            set_frame_size(fixed=size)
        elif mode == "2":
            println("Min：")
            minv = int(sys.stdin.readline().strip())
            println("Max：")
            maxv = int(sys.stdin.readline().strip())
            set_frame_size(min_size=minv, max_size=maxv)
        elif mode == "3":
            print("Action canceled.")
            
    elif choice == "10":
        show_traffic_items()
        println("\nSet traffic items：1) Add 2) Remove 0)Cancel")
        mode = sys.stdin.readline().strip()
        if mode == "1":
            println("\nTraffic Type：1) EthernetVlan 2) Raw 0)Cancel")
            TrafficType = sys.stdin.readline().strip()
            if TrafficType == "1":
                add_traffic_item()
            elif TrafficType == "2":
                add_raw_traffic_item()
            elif TrafficType == "3":
                print("Action canceled.")
        elif mode == "2":
            delete_traffic_items()
        elif mode == "3":
            print("Action canceled.")
    else:
        println("❌ Invalid input.")