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
    while True:
        print("="*100)
        print(f"📘 Current interface: Ethernet {port}/1")
        print("="*100)
        print(
            "Enter - Monitor current port status\n"
            "1 - Show status\n"
            "2 - Clean Counter\n"
            "3 - Re-Link (Link-down/up)\n"
            "4 - Set Speed\n"
            "5 - Change Port\n"
            "6 - Exit\n"
        )
        action = input("Select Action: ").strip()

        # -------------------------------------------------------
        interval = 0.1
        if action == "":
            show_loop(net_connect, port, interval, detail=True)

        elif action == "1":
            sub = input(
                "1 - Show All Status\n"
                "2 - Show All Description\n"
                "3 - Show Port Counters\n"
                "4 - Show PHY Detail\n"
                "5 - Show Transceiver Info\n"
                "Select: "
            ).strip()

            cmds = {
                "1": "show interface status",
                "2": "show interface description",
                "3": f"show interface ethernet {port}/1 counters",
                "4": f"show interface ethernet {port}/1 phy detail",
                "5": f"show interface ethernet {port}/1 transceiver detail",
            }
            cmd = cmds.get(sub)
            if not cmd:
                print("❌ Invalid selection.")
                continue
            output = net_connect.send_command_timing(cmd)
            print(output)
            log_command(cmd, output)

        elif action == "2":
            cmds = [
                f"clear counters ethernet {port}/1",
            ]
            for cmd in cmds:
                output = net_connect.send_command_timing(cmd)
                print(output)
                log_command(cmd, output)
                print("="*100)

        elif action == "3":
            RELINK_ACTION = input("1.Re-link 2.Link-down 3.Link-up:")
            if RELINK_ACTION == "1":
                net_connect.config_mode()   # localhost(Config)#:2
                output = net_connect.send_command_timing("interface ethernet {}/1".format(port))
                print("Link-down...")
                output = net_connect.send_command_timing("shutdown", delay_factor=1, max_loops=1)
                print("Link-up...")
                output = net_connect.send_command_timing("no shutdown")
                output = net_connect.send_config_set("show interface ethernet {}/1\n".format(port))
                cmd = input()
                output = net_connect.send_command_timing(cmd)
                print(output)
                
            if RELINK_ACTION == "2":
                net_connect.config_mode()   # localhost(Config)#:2
                output = net_connect.send_command_timing("interface ethernet {}/1".format(port))
                print("Link-down...")
                output = net_connect.send_command_timing("shutdown", delay_factor=1, max_loops=1)
                output = net_connect.send_config_set("show interface ethernet {}/1\n".format(port))
                print(output,"\n")
                
            if RELINK_ACTION == "3":
                net_connect.config_mode()   # localhost(Config)#:2
                output = net_connect.send_command_timing("interface ethernet {}/1".format(port))
                print("Link-up...")
                output = net_connect.send_command_timing("no shutdown")
                
                cmd = input()
                output = net_connect.send_command_timing(cmd)
                print(output)
                
                output = net_connect.send_config_set("show interface ethernet {}/1\n".format(port))
                print(output,"\n")
                


        elif action == "4":
            SPEED = input("Speed:")
            net_connect.config_mode()   # localhost(Config)#:2
            output = net_connect.send_command_timing("interface ethernet {}/1".format(port))
            output = net_connect.send_command_timing("speed {}".format(SPEED))
            print(output)

            cmd = input()
            output = net_connect.send_command_timing(cmd)
            print(output)

        elif action == "5":
            port = input("Change to new port: ")
        elif action == "6":
            print("👋 Exiting...")
            break
