import tkinter as tk
from tkinter import ttk, scrolledtext
import subprocess
import threading
import queue

# ======================
#  Dark Theme Colors
# ======================
BG_MAIN = "#1e1e1e"
BG_PANEL = "#252526"
BG_TITLE = "#333333"
FG_TEXT = "#ffffff"
BG_ENTRY = "#1f1f1f"


# ============================================================
#  Embedded Terminal Panel
# ============================================================

class PythonTerminal(tk.Frame):
    def __init__(self, parent, script_cmd, title, auto_clear=False):
        super().__init__(parent, bg=BG_PANEL)

        FONT_SMALL = ("Consolas", 8)
        self.script_cmd = script_cmd
        self.auto_clear = auto_clear
        self.alive = True

        self.title_label = tk.Label(
            self, text=title, anchor="w",
            bg=BG_TITLE, fg=FG_TEXT
        )
        self.title_label.pack(fill="x")

        self.output = scrolledtext.ScrolledText(
            self, wrap="word", height=10,
            bg=BG_MAIN, fg=FG_TEXT,
            insertbackground=FG_TEXT,
            font=FONT_SMALL
        )
        self.output.pack(fill="both", expand=True)
        self.output.configure(state="disabled")

        self.entry = tk.Entry(
            self, bg=BG_ENTRY, fg=FG_TEXT,
            insertbackground=FG_TEXT
        )
        self.entry.pack(fill="x")
        self.entry.bind("<Return>", self.send_input)

        self.queue = queue.Queue()

        # subprocess
        self.proc = subprocess.Popen(
            script_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace",
            bufsize=1
        )

        threading.Thread(target=self.reader, daemon=True).start()
        self.after(100, self.update_output)

    def clear_output(self):
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.configure(state="disabled")

    def append_text(self, text):
        if not self.alive:
            return
        self.output.configure(state="normal")
        self.output.insert("end", text)
        self.output.see("end")
        self.output.configure(state="disabled")

    def reader(self):
        for line in self.proc.stdout:
            if not self.alive:
                break
            self.queue.put(line)

    def update_output(self):
        if not self.alive:
            return

        try:
            while True:
                msg = self.queue.get_nowait()

                if self.auto_clear:
                    if msg.strip().startswith("🧩"): 
                        self.clear_output()
                    if msg.strip().startswith("📘"):
                        self.clear_output()
                    if ("Ethernet" in msg and "| " in msg):
                        self.clear_output()
                    if msg.strip().startswith("⏱"):
                        self.clear_output()
                    if ("===== Port Stats =====" in msg):
                        self.clear_output()

                self.append_text(msg)

        except queue.Empty:
            pass

        self.after(100, self.update_output)

    def send_input(self, event=None):
        if not self.alive:
            return

        text = self.entry.get() + "\n"
        self.entry.delete(0, "end")

        try:
            self.proc.stdin.write(text)
            self.proc.stdin.flush()
        except:
            self.append_text("[Process closed]\n")

    def terminate(self):
        self.alive = False
        try:
            self.proc.terminate()
        except:
            pass


# ============================================================
#  Main Unified Application
# ============================================================

class UnifiedApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ANIL Remote Control Tool")
        self.geometry("1900x1000")
        self.configure(bg=BG_MAIN)

        # ========= 第一排：Traffic Gen 選擇 =========
        f = tk.Frame(self, bg=BG_MAIN)
        f.pack(fill="x", pady=10)

        tk.Label(f, text="Topology:", fg="white", bg=BG_MAIN)\
            .grid(row=0, column=0, padx=5)

        self.traffic_mode = tk.StringVar(value="IXIA---SWITCH---DUT")
        cb = ttk.Combobox(f, textvariable=self.traffic_mode,
                          values=["IXIA---SWITCH---DUT","NIC---SWITCH---DUT", "IXIA---DUT", "NIC---DUT"], width=20)
        cb.grid(row=0, column=1, padx=5)
        self.traffic_mode.trace_add("write", self.update_second_row)

        # ========= 第二排：會根據 Traffic Gen 動態更新 =========
        self.config_frame = tk.Frame(self, bg=BG_MAIN)
        self.config_frame.pack(fill="x")
        self.update_second_row()  # 初始建立

        # ========= 下方 Grid =========
        self.grid_frame = tk.Frame(self, bg=BG_MAIN)
        self.grid_frame.pack(fill="both", expand=True)

        self.panels = []

        self.protocol("WM_DELETE_WINDOW", self.safe_exit)

    # ============================================================
    # 動態更新第二排
    # ============================================================

    def update_second_row(self, *args):
        for widget in self.config_frame.winfo_children():
            widget.destroy()

        mode = self.traffic_mode.get()

        if mode == "IXIA---SWITCH---DUT":
            self.build_ixia_row()
        elif mode == "NIC---SWITCH---DUT":
            self.build_ethagent_row()
        elif mode == "IXIA---DUT":
            self.build_ixia_without_swtich_row()
        elif mode == "NIC---DUT":
            self.build_ethagent_without_swtich_row()

    # ---------------------- IXIA UI ----------------------
    def build_ixia_row(self):
        f = self.config_frame

        tk.Label(f, text="IXIA:",
                 fg="white", bg=BG_MAIN).grid(row=0, column=0, padx=5)
        self.ixia = tk.StringVar(value="10.89.83.99")
        ttk.Combobox(f, textvariable=self.ixia,
                     values=["10.89.83.99","10.89.83.97"], width=20)\
            .grid(row=0, column=1, padx=5)

        tk.Label(f, text=" ", fg="white", bg=BG_MAIN)\
            .grid(row=0, column=2, padx=100)

        tk.Label(f, text="Switch:",
                 fg="white", bg=BG_MAIN).grid(row=0, column=3, padx=5)
        self.switch = tk.StringVar(value="Arista")
        ttk.Combobox(f, textvariable=self.switch,
                     values=["Arista"], width=20)\
            .grid(row=0, column=4, padx=5)

        tk.Label(f, text="Switch Port (to Traffic Gen):",
                 fg="white", bg=BG_MAIN).grid(row=0, column=5, padx=5)
        self.sc1 = tk.StringVar(value="13")
        ttk.Combobox(f, textvariable=self.sc1,
                     values=["1","2","3","13","16"], width=10)\
            .grid(row=0, column=6, padx=5)

        tk.Label(f, text="Switch Port (to DUT):",
                 fg="white", bg=BG_MAIN).grid(row=0, column=7, padx=5)
        self.sc2 = tk.StringVar(value="16")
        ttk.Combobox(f, textvariable=self.sc2,
                     values=["1","2","3","13","16"], width=10)\
            .grid(row=0, column=8, padx=5)

        tk.Label(f, text=" ", fg="white", bg=BG_MAIN)\
            .grid(row=0, column=9, padx=100)

        tk.Label(f, text="DUT IP:",
                 fg="white", bg=BG_MAIN).grid(row=0, column=10, padx=5)
        self.dut_ip = tk.StringVar(value="10.89.83.219:8086")
        ttk.Combobox(f, textvariable=self.dut_ip,
                     values=["10.89.83.219:8086"], width=20)\
            .grid(row=0, column=11, padx=5)
            
        tk.Label(f, text="DUT Slot:",
                 fg="white", bg=BG_MAIN).grid(row=0, column=12, padx=5)
        self.dut_slot = tk.StringVar(value="3")
        ttk.Combobox(f, textvariable=self.dut_slot,
                     values=["1","2","3","4","5"], width=10)\
            .grid(row=0, column=13, padx=5)
            
        tk.Label(f, text=" ", fg="white", bg=BG_MAIN)\
            .grid(row=0, column=14, padx=20)

        tk.Button(f, text="Start", command=self.start_panels)\
            .grid(row=0, column=15, padx=30)

    # ---------------------- IXIA without Switch UI ----------------------
    def build_ixia_without_swtich_row(self):
        f = self.config_frame

        tk.Label(f, text="IXIA:",
                 fg="white", bg=BG_MAIN).grid(row=0, column=0, padx=5)
        self.ixia = tk.StringVar(value="10.89.83.99")
        ttk.Combobox(f, textvariable=self.ixia,
                     values=["10.89.83.99","10.89.83.97"], width=20)\
            .grid(row=0, column=1, padx=5)

        tk.Label(f, text=" ", fg="white", bg=BG_MAIN)\
            .grid(row=0, column=2, padx=100)

        tk.Label(f, text="DUT IP:",
                 fg="white", bg=BG_MAIN).grid(row=0, column=10, padx=5)
        self.dut_ip = tk.StringVar(value="10.89.83.26:8086")
        ttk.Combobox(f, textvariable=self.dut_ip,
                     values=["10.89.83.26:8086"], width=20)\
            .grid(row=0, column=11, padx=5)
            
        tk.Label(f, text="DUT Slot:",
                 fg="white", bg=BG_MAIN).grid(row=0, column=12, padx=5)
        self.dut_slot = tk.StringVar(value="3")
        ttk.Combobox(f, textvariable=self.dut_slot,
                     values=["1","2","3","4","5"], width=10)\
            .grid(row=0, column=13, padx=5)
            
        tk.Label(f, text=" ", fg="white", bg=BG_MAIN)\
            .grid(row=0, column=14, padx=20)

        tk.Button(f, text="Start", command=self.start_panels)\
            .grid(row=0, column=15, padx=30)
    # ---------------------- EthAgent UI ----------------------
    def build_ethagent_row(self):
        f = self.config_frame

        tk.Label(f, text="TX IP:",
                 fg="white", bg=BG_MAIN).grid(row=0, column=0, padx=5)
        self.tx_ip = tk.StringVar(value="10.89.83.26:8087")
        ttk.Combobox(f, textvariable=self.tx_ip,
                     values=["10.89.83.26:8087"], width=20)\
            .grid(row=0, column=1, padx=5)
            
        tk.Label(f, text="TX Slot:",
                 fg="white", bg=BG_MAIN).grid(row=0, column=2, padx=5)
        self.tx_slot = tk.StringVar(value="4")
        ttk.Combobox(f, textvariable=self.tx_slot,
                     values=["1","2","3","4","5"], width=10)\
            .grid(row=0, column=3, padx=5)

        tk.Label(f, text=" ", fg="white", bg=BG_MAIN)\
            .grid(row=0, column=4, padx=70)

        tk.Label(f, text="Switch:",
                 fg="white", bg=BG_MAIN).grid(row=0, column=5, padx=5)
        self.switch = tk.StringVar(value="Arista")
        ttk.Combobox(f, textvariable=self.switch,
                     values=["Arista"], width=20)\
            .grid(row=0, column=6, padx=5)

        tk.Label(f, text="Switch Port (to Traffic Gen):",
                 fg="white", bg=BG_MAIN).grid(row=0, column=7, padx=5)
        self.sc1 = tk.StringVar(value="13")
        ttk.Combobox(f, textvariable=self.sc1,
                     values=["1","2","3","13","16"], width=10)\
            .grid(row=0, column=8, padx=5)

        tk.Label(f, text="Switch Port (to DUT):",
                 fg="white", bg=BG_MAIN).grid(row=0, column=9, padx=5)
        self.sc2 = tk.StringVar(value="16")
        ttk.Combobox(f, textvariable=self.sc2,
                     values=["1","2","3","13","16"], width=10)\
            .grid(row=0, column=10, padx=5)

        tk.Label(f, text=" ", fg="white", bg=BG_MAIN)\
            .grid(row=0, column=11, padx=70)

        tk.Label(f, text="DUT IP:",
                 fg="white", bg=BG_MAIN).grid(row=0, column=12, padx=5)
        self.dut_ip = tk.StringVar(value="10.89.83.26:8086")
        ttk.Combobox(f, textvariable=self.dut_ip,
                     values=["10.89.83.26:8086"], width=20)\
            .grid(row=0, column=13, padx=5)
            
        tk.Label(f, text="DUT Slot:",
                 fg="white", bg=BG_MAIN).grid(row=0, column=14, padx=5)
        self.dut_slot = tk.StringVar(value="3")
        ttk.Combobox(f, textvariable=self.dut_slot,
                     values=["1","2","3","4","5"], width=10)\
            .grid(row=0, column=15, padx=5)
            
        tk.Label(f, text=" ", fg="white", bg=BG_MAIN)\
            .grid(row=0, column=16, padx=20)

        tk.Button(f, text="Start", command=self.start_panels)\
            .grid(row=0, column=17, padx=30)
            
        # ---------------------- EthAgent without swtich UI ----------------------
    def build_ethagent_without_swtich_row(self):
        f = self.config_frame

        tk.Label(f, text="TX IP:",
                 fg="white", bg=BG_MAIN).grid(row=0, column=0, padx=5)
        self.tx_ip = tk.StringVar(value="10.89.83.26:8087")
        ttk.Combobox(f, textvariable=self.tx_ip,
                     values=["10.89.83.26:8087"], width=20)\
            .grid(row=0, column=1, padx=5)
            
        tk.Label(f, text="TX Slot:",
                 fg="white", bg=BG_MAIN).grid(row=0, column=2, padx=5)
        self.tx_slot = tk.StringVar(value="4")
        ttk.Combobox(f, textvariable=self.tx_slot,
                     values=["1","2","3","4","5"], width=10)\
            .grid(row=0, column=3, padx=5)

        tk.Label(f, text=" ", fg="white", bg=BG_MAIN)\
            .grid(row=0, column=4, padx=70)

        tk.Label(f, text="DUT IP:",
                 fg="white", bg=BG_MAIN).grid(row=0, column=12, padx=5)
        self.dut_ip = tk.StringVar(value="10.89.83.26:8086")
        ttk.Combobox(f, textvariable=self.dut_ip,
                     values=["10.89.83.26:8086"], width=20)\
            .grid(row=0, column=13, padx=5)
            
        tk.Label(f, text="DUT Slot:",
                 fg="white", bg=BG_MAIN).grid(row=0, column=14, padx=5)
        self.dut_slot = tk.StringVar(value="3")
        ttk.Combobox(f, textvariable=self.dut_slot,
                     values=["1","2","3","4","5"], width=10)\
            .grid(row=0, column=15, padx=5)
            
        tk.Label(f, text=" ", fg="white", bg=BG_MAIN)\
            .grid(row=0, column=16, padx=20)

        tk.Button(f, text="Start", command=self.start_panels)\
            .grid(row=0, column=17, padx=30)

    # ============================================================
    # Start Panels
    # ============================================================

    def start_panels(self):
        for w in self.grid_frame.winfo_children():
            w.destroy()
        self.panels.clear()

        mode = self.traffic_mode.get()
        ports = {"sc1": self.sc1.get(), "sc2": self.sc2.get()}
        dut_info = {"ip": self.dut_ip.get(), "slot": self.dut_slot.get()}

        if mode == "IXIA---SWITCH---DUT":
            scripts = [
                ["python", "IxNetwork_api.py"],
                ["python", "Switch_Control.py", "--port", ports["sc1"]],
                ["python", "Switch_Control.py", "--port", ports["sc2"]],
                ["python", "EthAgent_Control.py", "--ip", dut_info["ip"], "--slot", dut_info["slot"]],
                ["python", "Ixia_Status.py"],
                #["tclsh", "PortStats.tcl"],
                ["python", "Switch_Status.py", "--port", ports["sc1"]],
                ["python", "Switch_Status.py", "--port", ports["sc2"]],
            ]

            titles = [
                "Traffic Gen Control",
                f"Switch Control ({ports['sc1']}/1)",
                f"Switch Control ({ports['sc2']}/1)",
                "DUT EthAgent",
                "Traffic Port Stats",
                f"Switch Monitor ({ports['sc1']}/1)",
                f"Switch Monitor ({ports['sc2']}/1)",
            ]

            positions = [(0,0),(0,1),(0,2),(0,3),
                         (1,0),(1,1),(1,2)]
 
            for idx, (r, c) in enumerate(positions):
                auto_clear = idx in [0, 1, 2, 4, 5, 6]

                term = PythonTerminal(self.grid_frame,
                                      scripts[idx],
                                      titles[idx],
                                      auto_clear=auto_clear)

                # 展開 panel
                if idx == 3:
                    term.grid(row=r, column=c, rowspan=2,
                              sticky="nsew", padx=5, pady=5)
                else:
                    term.grid(row=r, column=c,
                              sticky="nsew", padx=5, pady=5)

                self.panels.append(term)

            for r in range(2):
                self.grid_frame.rowconfigure(r, weight=1)
            for c in range(4):
                self.grid_frame.columnconfigure(c, weight=1)


        elif mode == "NIC---SWITCH---DUT":
            tx_info = {"ip": self.tx_ip.get(), "slot": self.tx_slot.get()}

            scripts = [
                ["python", "EthAgent_Control.py", "--ip", tx_info["ip"], "--slot", tx_info["slot"]],
                ["python", "Switch_Control.py", "--port", ports["sc1"]],
                ["python", "Switch_Control.py", "--port", ports["sc2"]],
                ["python", "EthAgent_Control.py", "--ip", dut_info["ip"], "--slot", dut_info["slot"]],
                ["python", "Switch_Status.py", "--port", ports["sc1"]],
                ["python", "Switch_Status.py", "--port", ports["sc2"]],
            ]

            titles = [
                "Traffic Gen Control",
                f"Switch Control ({ports['sc1']}/1)",
                f"Switch Control ({ports['sc2']}/1)",
                "DUT EthAgent",
                f"Switch Monitor ({ports['sc1']}/1)",
                f"Switch Monitor ({ports['sc2']}/1)",
            ]

            positions = [(0,0),(0,1),(0,2),(0,3),
                         (1,1),(1,2)]

            for idx, (r, c) in enumerate(positions):
                auto_clear = idx in [0, 1, 2, 4, 5, 6]

                term = PythonTerminal(self.grid_frame,
                                      scripts[idx],
                                      titles[idx],
                                      auto_clear=auto_clear)

                # 展開 panel
                if idx in (0, 3):
                    term.grid(row=r, column=c, rowspan=2,
                              sticky="nsew", padx=5, pady=5)
                else:
                    term.grid(row=r, column=c,
                              sticky="nsew", padx=5, pady=5)

                self.panels.append(term)

            for r in range(2):
                self.grid_frame.rowconfigure(r, weight=1)
            for c in range(4):
                self.grid_frame.columnconfigure(c, weight=1)

        elif mode == "IXIA---DUT":
            scripts = [
                ["python", "IxNetwork_api.py"],
                ["python", "EthAgent_Control.py", "--ip", dut_info["ip"], "--slot", dut_info["slot"]],
                ["python", "IXIA_Status.py"],
            ]

            titles = [
                "Traffic Gen Control",
                "DUT EthAgent",
                "Traffic Port Stats",
            ]

            positions = [(0,0),(0,1),
                         (1,0)]
 
            for idx, (r, c) in enumerate(positions):
                auto_clear = idx in [0, 2]

                term = PythonTerminal(self.grid_frame,
                                      scripts[idx],
                                      titles[idx],
                                      auto_clear=auto_clear)

                # 展開 panel
                if idx == 1:
                    term.grid(row=r, column=c, rowspan=2,
                              sticky="nsew", padx=5, pady=5)
                else:
                    term.grid(row=r, column=c,
                              sticky="nsew", padx=5, pady=5)

                self.panels.append(term)

            for r in range(2):
                self.grid_frame.rowconfigure(r, weight=1)
            for c in range(2):
                self.grid_frame.columnconfigure(c, weight=1)
                
        elif mode == "NIC---DUT":
            tx_info = {"ip": self.tx_ip.get(), "slot": self.tx_slot.get()}

            scripts = [
                ["python", "EthAgent_Control.py", "--ip", tx_info["ip"], "--slot", tx_info["slot"]],
                ["python", "EthAgent_Control.py", "--ip", dut_info["ip"], "--slot", dut_info["slot"]],
            ]

            titles = [
                "Traffic Gen Control",
                "DUT EthAgent",
            ]

            positions = [(0,0),(0,1)]

            for idx, (r, c) in enumerate(positions):
                auto_clear = idx in [0,1]

                term = PythonTerminal(self.grid_frame,
                                      scripts[idx],
                                      titles[idx],
                                      auto_clear=auto_clear)

                # 展開 panel
                if idx == 1:
                    term.grid(row=r, column=c, rowspan=2,
                              sticky="nsew", padx=5, pady=5)
                else:
                    term.grid(row=r, column=c,
                              sticky="nsew", padx=5, pady=5)

                self.panels.append(term)

            for r in range(1):
                self.grid_frame.rowconfigure(r, weight=1)
            for c in range(2):
                self.grid_frame.columnconfigure(c, weight=1)

    # ============================================================
    # Exit
    # ============================================================

    def safe_exit(self):
        for p in self.panels:
            try:
                p.terminate()
            except:
                pass
        self.destroy()


# ============================================================
#  Run
# ============================================================

if __name__ == "__main__":
    UnifiedApp().mainloop()
