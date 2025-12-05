import paramiko
import time

USERNAME = "admin"
PASSWORD = "!Lad12345"

# Select IP
print("====================================================\n")
PDU_SEL = input("IP selection? 1:10.89.87.6  2:10.89.87.7\n").strip()
if PDU_SEL == "1":
    PDU_IP = "10.89.87.6"
elif PDU_SEL == "2":
    PDU_IP = "10.89.87.7"
else:
    print("❌ Invalid IP selection")
    exit(1)

# Connect to PDU
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    print(f"\n🔗 Connecting to {PDU_IP} ...")
    ssh.connect(PDU_IP, username=USERNAME, password=PASSWORD)
    shell = ssh.invoke_shell()
    time.sleep(1)
    shell.recv(1000)  # 清掉登入訊息
    print("✅ Connected successfully!\n")

    while True:
        print("====================================================")
        OUTLET_INDEX = input("PDU port number (e.g., 14):\n").strip()
        if not OUTLET_INDEX.isdigit():
            print("❌ Invalid port number")
            continue

        print("====================================================")
        action_sel = input("Action? 1: ON  2: OFF  3: CYCLE  4: SHOW STATUS  5: EXIT\n").strip()

        if action_sel == "1":
            ACTION = "on"
        elif action_sel == "2":
            ACTION = "off"
        elif action_sel == "3":
            ACTION = "cycle"
        elif action_sel == "4":
            ACTION = "SHOW"
        elif action_sel == "5":
            print("👋 Closing SSH connection and exiting...")
            break
        else:
            print("❌ Invalid action")
            continue

        if ACTION != "SHOW":
            cmd = f"power outlets {OUTLET_INDEX} {ACTION}\n"
            print(f"[Send] {cmd.strip()}")
            shell.send(cmd)
            time.sleep(1)
            shell.send("y\n")
            time.sleep(1)
            shell.recv(100)

        shell.send(f"show outlets {OUTLET_INDEX}\n")
        time.sleep(1)
        output = shell.recv(5000).decode()
        print("\n=== CLI Output ===")
        print(output)

except Exception as e:
    print("❌ Error：", str(e))

finally:
    ssh.close()
    print("🔒 SSH disconnected.")