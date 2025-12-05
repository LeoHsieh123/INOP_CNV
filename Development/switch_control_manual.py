from netmiko import ConnectHandler

arista_switch = {
    'device_type': 'arista_eos',
    'ip': '10.89.83.55',
    'username': 'admin',
    'password': 'Intel@123',
}


try:
    net_connect = ConnectHandler(**arista_switch)
    print("✅ Connected successfully!\n")    # localhost>

    while True:
        output = net_connect.enable()   # localhost#:
        net_connect.config_mode()   # localhost(Config)#:
        while True:
            cmd = input("localhost(config)#:")
            if cmd.lower() in ["exit", "end"]:
                output = net_connect.send_config_set("disable") 
                break
            #output = net_connect.send_command(cmd, expect_string=r"\(config.*\)#")
            output = net_connect.send_command_timing(cmd)
            print(output)
         
        cmd = input("localhost#:")
        if cmd.lower() in ["exit", "end"]:
            break
        

except Exception as e:
    print("❌ Error：", str(e))

finally:
    net_connect.save_config()
    net_connect.disconnect()
    print("🔒 Arista disconnected.")