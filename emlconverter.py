"""
Maildir → EML Bulk Converter V3.3 (Direct Mailbox Mode)
Includes UI Icon Support, User Guide, and Creator Signature.
"""
 
import os
import sys
import mailbox
import threading
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
from datetime import datetime
from email.utils import parsedate_to_datetime

# ─────────────────────────── helpers ────────────────────────────

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
 
def sanitize(name, maxlen: int = 60) -> str:
    if not name:
        return "unknown"
    name = str(name).replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    clean_name = "".join(c for c in name if c not in r'\/:*?"<>|')
    return " ".join(clean_name.split())[:maxlen].strip() or "unknown"
 
def find_all_maildirs(root_path):
    maildirs = []
    root_path = os.path.abspath(root_path)
    if os.path.isdir(os.path.join(root_path, "cur")):
        maildirs.append(("INBOX", root_path))
    try:
        for entry in sorted(os.scandir(root_path), key=lambda e: e.name):
            if entry.is_dir():
                if entry.name in ['cur', 'new', 'tmp']:
                    continue
                if os.path.isdir(os.path.join(entry.path, "cur")):
                    clean_name = entry.name.lstrip(".")
                    maildirs.append((clean_name, entry.path))
    except Exception:
        pass
    return maildirs
 
# ─────────────────────────── core converter ─────────────────────
 
def convert_all(source_root: str, output_root: str, log_fn, progress_fn, done_fn):
    folders = find_all_maildirs(source_root)
    if not folders:
        log_fn("⚠  No mail folders found. Click 'How to Use' for help.")
        done_fn({"folders": 0, "saved": 0, "skipped": 0})
        return
 
    log_fn(f"Detected {len(folders)} mail folder(s) to process.\n")
    total_msgs = 0
    all_jobs = []
    for folder_name, folder_path in folders:
        try:
            mbox = mailbox.Maildir(folder_path, factory=None, create=False)
            count = len(mbox)
            total_msgs += count
            all_jobs.append((folder_name, folder_path, count))
        except Exception:
            pass
 
    log_fn(f"Total emails to convert: {total_msgs}\n{'─'*50}")
    saved = skipped = folders_done = 0
    processed = 0
 
    for folder_name, folder_path, _ in all_jobs:
        out_dir = os.path.join(output_root, sanitize(folder_name))
        os.makedirs(out_dir, exist_ok=True)
        try:
            mbox = mailbox.Maildir(folder_path, factory=None, create=False)
        except Exception as e:
            log_fn(f"  ✗ Cannot open {folder_name}: {e}")
            continue
 
        log_fn(f"\n📁 {folder_name}  ({len(mbox)} msgs)")
        folders_done += 1
 
        for key, msg in mbox.items():
            processed += 1
            if processed % 10 == 0 or processed == total_msgs:
                progress_fn(processed, total_msgs)
            try:
                raw_date = msg.get("Date", "")
                try:
                    dt = parsedate_to_datetime(raw_date)
                    date_str = dt.strftime("%Y-%m-%d_%H-%M") 
                except Exception:
                    date_str = "NoDate"
                
                raw_from = msg.get("From", "UnknownSender")
                clean_from = sanitize(raw_from, 35)
                raw_subj = msg.get("Subject", "NoSubject")
                clean_subj = sanitize(raw_subj, 60)
                
                msg_num = f"{processed:05d}"
                base_name = f"{msg_num}_{date_str}_{clean_from}_{clean_subj}"
                filename = f"{sanitize(base_name, 150)}.eml"
                filepath = os.path.join(out_dir, filename)
                
                with open(filepath, "wb") as f:
                    f.write(msg.as_bytes())
                
                original_file_path = os.path.join(folder_path, "cur", key)
                if not os.path.exists(original_file_path):
                    original_file_path = os.path.join(folder_path, "new", key)
                if os.path.exists(original_file_path):
                    stat = os.stat(original_file_path)
                    os.utime(filepath, (stat.st_atime, stat.st_mtime))
                saved += 1
            except Exception as e:
                log_fn(f"  ⚠ Skipped msg {key}: {e}")
                skipped += 1
 
    done_fn({"folders": folders_done, "saved": saved, "skipped": skipped})
 
# ─────────────────────────── GUI ────────────────────────────────
 
class App(tk.Tk):
    BG       = "#1a1a2e"
    SURFACE  = "#16213e"
    ACCENT   = "#0f3460"
    HIGHLIGHT= "#e94560"
    TEXT     = "#eaeaea"
    MUTED    = "#8892a4"
    SUCCESS  = "#4ade80"
    WARNING  = "#facc15"
    FONT     = ("Consolas", 10)
    FONT_H   = ("Segoe UI", 11, "bold")
 
    def __init__(self):
        super().__init__()
        self.title("Maildir → EML Converter")
        self.geometry("780x680")
        self.resizable(True, True)
        self.configure(bg=self.BG)

        try:
            icon_path = resource_path("rocket.ico")
            self.iconbitmap(icon_path)
        except Exception:
            pass 

        self._build_ui()
        self._running = False
 
    def _build_ui(self):
        self._style()
        
        # --- NEW: Signature Footer at the very bottom ---
        footer = tk.Frame(self, bg=self.BG, pady=10)
        footer.pack(side="bottom", fill="x")
        tk.Label(footer, text="Made with ♥️ by Mahmoud Hamdy", font=("Segoe UI", 10), fg=self.MUTED, bg=self.BG).pack()

        # Header
        hdr = tk.Frame(self, bg=self.ACCENT, padx=20, pady=12)
        hdr.pack(fill="x", side="top")
        tk.Label(hdr, text="✉  Maildir → EML Bulk Converter", font=("Segoe UI", 14, "bold"), fg=self.TEXT, bg=self.ACCENT).pack(side="left")
        tk.Label(hdr, text="V3.3", font=("Segoe UI", 9), fg=self.MUTED, bg=self.ACCENT).pack(side="right")
 
        # Paths
        paths_frame = tk.Frame(self, bg=self.BG, padx=20, pady=14)
        paths_frame.pack(fill="x", side="top")
        self._src_var = tk.StringVar()
        self._dst_var = tk.StringVar()
        self._path_row(paths_frame, "Source Mailbox Folder:", self._src_var, 0)
        self._path_row(paths_frame, "Output Folder:",         self._dst_var, 1)
 
        # Progress
        prog_frame = tk.Frame(self, bg=self.BG, padx=20)
        prog_frame.pack(fill="x", side="top")
        self._prog_label = tk.Label(prog_frame, text="Ready.", font=self.FONT, fg=self.MUTED, bg=self.BG, anchor="w")
        self._prog_label.pack(fill="x")
        self._pbar = ttk.Progressbar(prog_frame, style="Custom.Horizontal.TProgressbar", length=740, mode="determinate")
        self._pbar.pack(fill="x", pady=(4, 10))
 
        # Buttons
        btn_frame = tk.Frame(self, bg=self.BG, padx=20, pady=10)
        btn_frame.pack(fill="x", side="top")
        self._start_btn = tk.Button(btn_frame, text="▶  Start Conversion", font=("Segoe UI", 10, "bold"), bg=self.HIGHLIGHT, fg="white", activebackground="#c73652", activeforeground="white", relief="flat", padx=20, pady=8, cursor="hand2", command=self._start)
        self._start_btn.pack(side="left")
        tk.Button(btn_frame, text="Clear Log", font=("Segoe UI", 10), bg=self.ACCENT, fg=self.TEXT, activebackground=self.HIGHLIGHT, activeforeground="white", relief="flat", padx=16, pady=8, cursor="hand2", command=self._clear_log).pack(side="left", padx=(10, 0))
        tk.Button(btn_frame, text="❓ How to Use", font=("Segoe UI", 10, "bold"), bg="#2563eb", fg="white", activebackground="#1d4ed8", activeforeground="white", relief="flat", padx=16, pady=8, cursor="hand2", command=self._show_help).pack(side="left", padx=(10, 0))
        self._status = tk.Label(btn_frame, text="", font=("Segoe UI", 10, "bold"), fg=self.SUCCESS, bg=self.BG)
        self._status.pack(side="right")

        # Log Frame
        log_frame = tk.Frame(self, bg=self.BG, padx=20)
        log_frame.pack(fill="both", expand=True, side="top")
        tk.Label(log_frame, text="Log", font=self.FONT_H, fg=self.MUTED, bg=self.BG).pack(anchor="w")
        self._log = scrolledtext.ScrolledText(log_frame, font=("Consolas", 9), bg=self.SURFACE, fg=self.TEXT, insertbackground=self.TEXT, relief="flat", padx=10, pady=8, state="disabled")
        self._log.pack(fill="both", expand=True, pady=(4, 12))
 
    def _path_row(self, parent, label, var, row):
        tk.Label(parent, text=label, font=self.FONT_H, fg=self.TEXT, bg=self.BG, width=22, anchor="w").grid(row=row, column=0, pady=4, sticky="w")
        entry = tk.Entry(parent, textvariable=var, font=self.FONT, bg=self.SURFACE, fg=self.TEXT, insertbackground=self.TEXT, relief="flat", width=52)
        entry.grid(row=row, column=1, padx=(6, 6), ipady=5)
        tk.Button(parent, text="Browse…", font=self.FONT, bg=self.ACCENT, fg=self.TEXT, activebackground=self.HIGHLIGHT, activeforeground="white", relief="flat", padx=10, pady=4, cursor="hand2", command=lambda v=var: self._browse(v)).grid(row=row, column=2)
 
    def _style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("Custom.Horizontal.TProgressbar", troughcolor=self.SURFACE, background=self.HIGHLIGHT, bordercolor=self.BG, lightcolor=self.HIGHLIGHT, darkcolor=self.HIGHLIGHT)
 
    def _browse(self, var):
        path = filedialog.askdirectory(title="Select folder")
        if path:
            var.set(os.path.normpath(path))
            
    def _show_help(self):
        help_win = tk.Toplevel(self)
        help_win.title("How to Use This Converter")
        help_win.geometry("550x380")
        help_win.configure(bg=self.BG)
        
        try:
            icon_path = resource_path("rocket.ico")
            help_win.iconbitmap(icon_path)
        except Exception:
            pass
            
        help_win.grab_set() 
        
        tk.Label(help_win, text="How to Use This Tool", font=("Segoe UI", 16, "bold"), bg=self.BG, fg=self.TEXT).pack(pady=(20, 10))
        
        instructions = (
            "Step 1: Select the Source Mailbox Folder\n"
            "Click the first 'Browse...' button and choose the main folder that contains the user's email data (for example, a folder named 'a.sayed').\n\n"
            
            "Step 2: Select the Output Folder\n"
            "Click the second 'Browse...' button and choose where you want the readable .eml files to be saved. It is highly recommended to create a new, empty folder for this.\n\n"
            
            "Step 3: Start Conversion\n"
            "Click the red 'Start Conversion' button. The tool will automatically sort the emails into their correct folders. Wait for the progress bar to reach 100%.\n\n"
            
            "🔒 Safe & Secure: This tool only copies your data. Your original email files are completely safe and will not be modified or deleted."
        )
        
        lbl = tk.Label(help_win, text=instructions, font=("Segoe UI", 11), bg=self.BG, fg=self.TEXT, justify="left", wraplength=480)
        lbl.pack(padx=20, pady=5, anchor="w")
        
        tk.Button(help_win, text="Got it!", font=("Segoe UI", 11, "bold"), bg=self.HIGHLIGHT, fg="white", activebackground="#c73652", activeforeground="white", relief="flat", padx=30, pady=6, cursor="hand2", command=help_win.destroy).pack(pady=20)
 
    def _clear_log(self):
        self._log.configure(state="normal")
        self._log.delete("1.0", "end")
        self._log.configure(state="disabled")
 
    def _log_write(self, msg):
        def _do():
            self._log.configure(state="normal")
            self._log.insert("end", msg + "\n")
            self._log.see("end")
            self._log.configure(state="disabled")
        self.after(0, _do)
 
    def _update_progress(self, cur, tot):
        def _do():
            pct = int(cur / tot * 100) if tot else 0
            self._pbar["value"] = pct
            self._prog_label.config(text=f"Processing: {cur} / {tot}  ({pct}%)", fg=self.TEXT)
        self.after(0, _do)
 
    def _on_done(self, stats):
        def _do():
            self._running = False
            self._start_btn.config(state="normal", text="▶  Start Conversion")
            self._pbar["value"] = 100
            summary = (f"\n{'═'*50}\n✅  Done!  Folders Processed: {stats['folders']}  |  Saved: {stats['saved']}  |  Skipped: {stats['skipped']}\nOutput → {self._dst_var.get()}\n{'═'*50}")
            self._log_write(summary)
            self._status.config(text=f"✓ {stats['saved']} emails exported", fg=self.SUCCESS)
            self._prog_label.config(text=f"Finished — {stats['saved']} emails saved, {stats['skipped']} skipped.", fg=self.SUCCESS)
        self.after(0, _do)
 
    def _start(self):
        src = self._src_var.get().strip()
        dst = self._dst_var.get().strip()
        if not src or not os.path.isdir(src):
            self._flash_error("⚠  Please select a valid source folder.")
            return
        if not dst:
            self._flash_error("⚠  Please select an output folder.")
            return
        if self._running:
            return
        self._running = True
        self._status.config(text="")
        self._start_btn.config(state="disabled", text="⏳  Running…")
        self._pbar["value"] = 0
        self._prog_label.config(text="Starting…", fg=self.TEXT)
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._log_write(f"{'═'*50}\n  Conversion started: {ts}\n  Source : {src}\n  Output : {dst}\n{'═'*50}\n")
        t = threading.Thread(target=convert_all, args=(src, dst, self._log_write, self._update_progress, self._on_done), daemon=True)
        t.start()
 
    def _flash_error(self, msg):
        self._status.config(text=msg, fg=self.WARNING)
 
if __name__ == "__main__":
    app = App()
    app.mainloop()