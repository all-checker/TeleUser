import requests
from bs4 import BeautifulSoup
from colorama import Fore, Style
import os
import tkinter as tk
from tkinter import scrolledtext, filedialog
import threading

pause_event = threading.Event()
pause_event.set()

HEADER_TEXT = "Telegram Username Checker Coded by https://t.me/malwaredot\n"

def check_username_availability(username):
    url = f"https://fragment.com/username/{username}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        status_div = soup.find("div", class_="table-cell-value tm-value tm-status-unavail")
        status_span_avail = soup.find("span", class_="tm-section-header-status tm-status-avail")
        status_span_taken = soup.find("span", class_="tm-section-header-status tm-status-taken")
        if status_span_avail:
            return "On auction"
        elif status_span_taken:
            return "taken"
        elif status_div:
            return Fore.GREEN + "Unused Username" + Style.RESET_ALL
        else:
            return "available"
    except requests.exceptions.RequestException as e:
        return f"Error: {e}"

def ensure_file_with_header(file_path):
    if not os.path.exists(file_path):
        with open(file_path, "w") as file:
            file.write(HEADER_TEXT)

def process_usernames(input_file, checked_file, unused_file, log_area):
    ensure_file_with_header(checked_file)
    ensure_file_with_header(unused_file)
    checked_usernames = set()
    if os.path.exists(checked_file):
        with open(checked_file, "r") as file:
            checked_usernames = set(file.read().splitlines()[1:])
    try:
        with open(input_file, "r") as file:
            usernames = file.read().splitlines()
        total_usernames = len(usernames)
        processed_count = 0
        for username in usernames:
            pause_event.wait()
            if username in checked_usernames:
                log_area.insert(tk.END, f"Skipping {username}, already checked.\n")
                log_area.see(tk.END)
                processed_count += 1
                progress_label.config(text=f"Progress: {processed_count}/{total_usernames} ({(processed_count / total_usernames) * 100:.2f}%)")
                continue
            status = check_username_availability(username)
            if "Unused Username" in status:
                log_area.insert(tk.END, f"{username}: {status}\n", "green")
                with open(unused_file, "a") as unused:
                    unused.write(username + "\n")
            else:
                log_area.insert(tk.END, f"{username}: {status}\n")
            log_area.see(tk.END)
            with open(checked_file, "a") as checked:
                checked.write(username + "\n")
            processed_count += 1
            progress_label.config(text=f"Progress: {processed_count}/{total_usernames} ({(processed_count / total_usernames) * 100:.2f}%)")
    except FileNotFoundError:
        log_area.insert(tk.END, f"Error: {input_file} not found.\n")
        log_area.see(tk.END)
    except Exception as e:
        log_area.insert(tk.END, f"An unexpected error occurred: {e}\n")
        log_area.see(tk.END)

def start_tool():
    input_file = filedialog.askopenfilename(title="Select Input File", filetypes=[("Text Files", "*.txt")])
    if not input_file:
        return
    checked_file = "checked_usernames.txt"
    unused_file = "unused_usernames.txt"
    log_area.delete(1.0, tk.END)
    log_area.insert(tk.END, "Processing started...\n")
    threading.Thread(target=process_usernames, args=(input_file, checked_file, unused_file, log_area)).start()

def toggle_pause():
    if pause_event.is_set():
        pause_event.clear()
        pause_button.config(text="Resume")
        log_area.insert(tk.END, "Processing paused.\n")
    else:
        pause_event.set()
        pause_button.config(text="Pause")
        log_area.insert(tk.END, "Processing resumed.\n")

root = tk.Tk()
root.title("Telegram Username Checker By @MalwareDot")
root.geometry("600x800")
root.configure(bg="#383838")
root.resizable(False, False)
banner_text = """


████████╗███████╗██╗     ███████╗██╗   ██╗███████╗███████╗██████╗ 
╚══██╔══╝██╔════╝██║     ██╔════╝██║   ██║██╔════╝██╔════╝██╔══██╗
   ██║   █████╗  ██║     █████╗  ██║   ██║███████╗█████╗  ██████╔╝
   ██║   ██╔══╝  ██║     ██╔══╝  ██║   ██║╚════██║██╔══╝  ██╔══██╗
   ██║   ███████╗███████╗███████╗╚██████╔╝███████║███████╗██║  ██║
   ╚═╝   ╚══════╝╚══════╝╚══════╝ ╚═════╝ ╚══════╝╚══════╝╚═╝  ╚═╝
                                                                  


"""
banner_label = tk.Label(root, text=banner_text, bg="#383838", fg="magenta", font=("Consolas", 10), justify="center")
banner_label.pack(pady=10)

progress_label = tk.Label(root, text="Progress: 0/0 (0.00%)", bg="#383838", fg="white", font=("Arial", 12))
progress_label.pack(pady=5)

start_button = tk.Button(root, text="Start", command=start_tool, bg="#5A5A5A", fg="white", font=("Arial", 12), relief="solid", borderwidth=0)
start_button.pack(pady=10)

pause_button = tk.Button(root, text="Pause", command=toggle_pause, bg="#5A5A5A", fg="white", font=("Arial", 12), relief="solid", borderwidth=0)
pause_button.pack(pady=10)

log_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, bg="#2E2E2E", fg="white", font=("Consolas", 10))
log_area.tag_config("green", foreground="green")
log_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

root.mainloop()