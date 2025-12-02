import os

#os.system("./install")
os.system("systemctl stop firewalld")

os.system("gnome-terminal -- sh -c './ethagentIL64E /PORT:8086'")

os.system("gnome-terminal -- sh -c './ethagentIL64E /PORT:8087'")

os.system("gnome-terminal -- sh -c './ethagentIL64E /PORT:8088'")

os.system("gnome-terminal -- sh -c './ethagentIL64E /PORT:8089'")

os.system("gnome-terminal -- sh -c './ethagentIL64E /PORT:8096'")

os.system("gnome-terminal -- sh -c './ethagentIL64E /PORT:8097'")

os.system("gnome-terminal -- sh -c './ethagentIL64E /PORT:8098'")

os.system("gnome-terminal -- sh -c './ethagentIL64E /PORT:8099'")
