import subprocess
import sys

tcl_script = "PortStats.tcl"

# 啟動 Tcl 並即時讀取 stdout
process = subprocess.Popen(
    ["tclsh", tcl_script],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1   # line-buffered，這行很重要
)

print("=== REAL-TIME TCL OUTPUT ===")

# 持續讀每一行 → 即時顯示
for line in process.stdout:
    print(line, end="")    # end=""：避免多一行

process.wait()
print("\n=== TCL EXITED ===")
