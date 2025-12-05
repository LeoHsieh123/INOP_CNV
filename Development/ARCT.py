import subprocess

# 你的 6 個腳本
scripts = [
    "C:\\Users\\lchiench\\OneDrive - Intel Corporation\\Desktop\\ssh control\\IXIA_ixnetwork_auto.py",
    "C:\\Users\\lchiench\\OneDrive - Intel Corporation\\Desktop\\ssh control\\switch_control_auto.py",
    "C:\\Users\\lchiench\\OneDrive - Intel Corporation\\Desktop\\ssh control\\switch_control_auto.py",
    "C:\\Users\\lchiench\\OneDrive - Intel Corporation\\Desktop\\ssh control\\IXIA_rest_api.py",
    "C:\\Users\\lchiench\\OneDrive - Intel Corporation\\Desktop\\ssh control\\switch_control_show_status.py",
    "C:\\Users\\lchiench\\OneDrive - Intel Corporation\\Desktop\\ssh control\\switch_control_show_status.py"
]

def run(script):
    return f'python "{script}"'

cmd = (
    f'wt new-tab --title "1" --command {run(scripts[0])} ; '
    f'split-pane -V --size 0.66 --title "2" --command {run(scripts[1])} ; '
    f'split-pane -V --size 0.50 --title "3" --command {run(scripts[2])} ; '
    f'focus-pane --target 0 ; '
    f'split-pane -H --size 0.50 --title "4" --command {run(scripts[3])} ; '
    f'focus-pane --target 1 ; '
    f'split-pane -H --size 0.50 --title "5" --command {run(scripts[4])} ; '
    f'focus-pane --target 2 ; '
    f'split-pane -H --size 0.50 --title "6" --command {run(scripts[5])}'
)

print("Launching 2x2 Windows Terminal grid...")

subprocess.Popen(
    cmd,
    shell=True,
    creationflags=subprocess.CREATE_NO_WINDOW   # 不開 PowerShell 視窗
)
