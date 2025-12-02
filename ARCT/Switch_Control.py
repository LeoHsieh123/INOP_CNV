import argparse
import sys
import time
import os
from netmiko import ConnectHandler

# UTF-8 safe
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

def println(msg=""):
    print(msg, flush=True)

parser = argparse.ArgumentParser()
parser.add_argument("--port", type=str, required=True)
args = parser.parse_args()

PORT = args.port


def connect_arista(ip, user, pwd):
    dev = {
        'device_type': 'arista_eos',
        'ip': ip,
        'username': user,
        'password': pwd,
    }
    println(f"🔌 Connecting to {ip} ...")
    net = ConnectHandler(**dev)
    net.enable()
    println("✅ Connected successfully!\n")
    return net


def send_with_confirm(net, cmd, confirm_keyword="[y/N]", reply="y"):
    println(f"\n➡️ Running: {cmd}")
    output = net.send_command_timing(cmd)

    if confirm_keyword in output:
        println("⚠️ Confirm required → auto reply 'y'")
        output += net.send_command_timing(reply)

    println(output)
    return output


# ---------------- MAIN ----------------
if __name__ == "__main__":
    net_connect = connect_arista("10.89.83.55", "admin", "Intel@123")
    port = PORT

    while True:
        println("=" * 50)
        println(f"📘 Current interface: Ethernet {port}/1")
        println("=" * 50)
        println(
            "1 - Clean Counter\n"
            "2 - Re-Link (Link-down/up)\n"
            "3 - Set Speed\n"
            "4 - Show Vlan\n"
            "5 - VLAN + Static MAC Setting\n"
            "6 - Delete VLAN + Static MAC\n"
        )
        println("=" * 50)
        print("Select Action: ", flush=True)

        action = sys.stdin.readline().strip()
        # ---------------------------
        # 1. Clean Counter
        # ---------------------------
        if action == "1":
            cmd = f"clear counters ethernet {port}/1"
            output = net_connect.send_command_timing(cmd)
            println(output)

        # ---------------------------
        # 2. Re-link
        # ---------------------------
        elif action == "2":
            println("\n1.Re-link  2.Link-down  3.Link-up")
            relink = sys.stdin.readline().strip()

            send_with_confirm(net_connect, "configure terminal")
            send_with_confirm(net_connect, f"interface ethernet {port}/1")

            if relink == "1":
                println("🔻 Link-down...")
                send_with_confirm(net_connect, "shutdown")

                println("🔺 Link-up...")
                send_with_confirm(net_connect, "no shutdown")

            elif relink == "2":
                println("🔻 Link-down...")
                send_with_confirm(net_connect, "shutdown")

            elif relink == "3":
                println("🔺 Link-up...")
                send_with_confirm(net_connect, "no shutdown")

            else:
                println("❌ Invalid option")

        # ---------------------------
        # 3. Set Speed
        # ---------------------------
        elif action == "3":
            println("\nSpeed:")
            SPEED = sys.stdin.readline().strip()

            net_connect.config_mode()
            send_with_confirm(net_connect, f"interface ethernet {port}/1")
            send_with_confirm(net_connect, f"speed {SPEED}")

        # ---------------------------
        # 5. VLAN + Static MAC Setting
        # ---------------------------
        elif action == "4":
            vlan_all = net_connect.send_command(f"show vlan")
            println(vlan_all)
            println("\n Press any key to continue")
            sys.stdin.readline().strip()
        
        elif action == "5":
            vlan_all = net_connect.send_command(f"show vlan")
            println(vlan_all)
            
            println("\n🔧 Enter VLAN ID:")
            vlan_id = sys.stdin.readline().strip()

            println("🔧 Enter Port A (ex: 13):")
            port_a = sys.stdin.readline().strip()

            println("🔧 Enter Port B (ex: 16):")
            port_b = sys.stdin.readline().strip()

            println("🔧 Enter MAC of Port A (format: xxxx.xxxx.xxxx):")
            mac_a = sys.stdin.readline().strip()

            println("🔧 Enter MAC of Port B (format: xxxx.xxxx.xxxx):")
            mac_b = sys.stdin.readline().strip()

            send_with_confirm(net_connect, "configure terminal")

            # Create VLAN
            send_with_confirm(net_connect, f"vlan {vlan_id}")

            # Access VLAN setting
            send_with_confirm(net_connect, f"interface Ethernet{port_a}/1")
            send_with_confirm(net_connect, f"switchport access vlan {vlan_id}")

            send_with_confirm(net_connect, f"interface Ethernet{port_b}/1")
            send_with_confirm(net_connect, f"switchport access vlan {vlan_id}")

            # Static MAC mapping (A <-> B)
            send_with_confirm(
                net_connect,
                f"mac address-table static {mac_b} vlan {vlan_id} interface Ethernet{port_a}/1"
            )
            send_with_confirm(
                net_connect,
                f"mac address-table static {mac_a} vlan {vlan_id} interface Ethernet{port_b}/1"
            )

            println("\n✅ VLAN + Static MAC setting completed!")


        # ---------------------------
        # 6. Delete VLAN + Static MAC
        # ---------------------------
        elif action == "6":
            vlan_all = net_connect.send_command(f"show vlan")
            println(vlan_all)
            
            println("\n🗑️ Enter VLAN ID to DELETE:")
            vlan_id = sys.stdin.readline().strip()

            println("🔧 Enter Port A (ex: 13):")
            port_a = sys.stdin.readline().strip()

            println("🔧 Enter Port B (ex: 16):")
            port_b = sys.stdin.readline().strip()

            println("🔧 Enter MAC of Port A:")
            mac_a = sys.stdin.readline().strip()

            println("🔧 Enter MAC of Port B:")
            mac_b = sys.stdin.readline().strip()

            send_with_confirm(net_connect, "configure terminal")

            # Delete static MAC
            send_with_confirm(
                net_connect,
                f"no mac address-table static {mac_b} vlan {vlan_id} interface Ethernet{port_a}/1"
            )
            send_with_confirm(
                net_connect,
                f"no mac address-table static {mac_a} vlan {vlan_id} interface Ethernet{port_b}/1"
            )

            # Restore ports to VLAN 1
            '''send_with_confirm(net_connect, f"interface Ethernet{port_a}/1")
            send_with_confirm(net_connect, "switchport access vlan 1")

            send_with_confirm(net_connect, f"interface Ethernet{port_b}/1")
            send_with_confirm(net_connect, "switchport access vlan 1")'''

            # Delete VLAN
            send_with_confirm(net_connect, f"no vlan {vlan_id}")

            println("\n✅ VLAN + Static MAC removed successfully!")

        # ---------------------------
        else:
            println("❌ Invalid input.")
