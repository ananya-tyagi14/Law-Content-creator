import webbrowser
import os
import time
import pandas as pd
import matplotlib.pyplot as plt
import threading
import queue
import tkinter as tk
import sys
import pygetwindow as gw

download_queue = queue.Queue()
file_downloads = []

def open_google_trends():

    chrome_path = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"

    webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(chrome_path))
    
    url = "https://trends.google.com/trends/"
    
    print("Opening Google Trends...")
    webbrowser.get('chrome').open(url)


def wait_for_download(download_folder, extension=".csv"):

    print("waiting for user to download file...")
    already_exists = set(os.listdir(download_folder))
    while True:
        time.sleep(1)     
        current_files = set(os.listdir(download_folder))
        new_files = current_files - already_exists

        for new_file in new_files:
            if new_file.endswith(extension):
                print(f"Detected new download: {new_file}")
                return os.path.join(download_folder, new_file)
            

def process_downloads():
    downloads_folder = os.path.expanduser("~/Downloads")

    while True:
        downloaded_file = wait_for_download(downloads_folder, extension=".csv")    
        print("File has been downloaded successfully.")
        download_queue.put(downloaded_file)
            

def visualise_data(file_path):

    df = pd.read_csv(file_path, skiprows=1)

    print("columns in the CSV:", df.columns.tolist())

    time_col = df.columns[0]
    df.rename(columns={time_col: 'time'}, inplace=True)
    df['time'] = pd.to_datetime(df['time'])

    fig, ax = plt.subplots()
    
    if len(df.columns) == 2:
        trend_col = df.columns[1]

        ax.plot(df['time'], df[trend_col], marker='o', linestyle='-')
        ax.set_xlabel('Time')
        ax.set_ylabel('Search Interest')
        ax.set_title(f'Google Trends: {trend_col}')
        ax.grid(True)
        
        fig.tight_layout()
        
        plt.show(block=False)
        plt.pause(0.1)
        
    else:
        for col in df.columns[1:]:
            ax.plot(df['time'], df[col], marker='o', linestyle='-', label=col)
            
        ax.set_xlabel('Time')
        ax.set_ylabel('Search Interest')
        ax.set_title('Google Trends Comparison')
        ax.grid(True)
        ax.legend()
        fig.tight_layout()
        plt.show(block=False)
        plt.pause(0.1)


def analyse_individual(files):

    results ={}
    for file in files:
        try:
            df = pd.read_csv(file, skiprows=1)
            print(f"File: {file} has columns: {df.columns.tolist()}")

            if len(df.columns) != 2:
                print(f"File {file} does not have at least 2 columns. Skipping.")
                continue

            time_col = df.columns[0]
            trend_col = df.columns[1]

            df.rename(columns={time_col: 'time'}, inplace=True)
            df['time'] = pd.to_datetime(df['time'])

            search_avg = df[trend_col].mean()
            results[trend_col] = search_avg
        except Exception as e:
            print(f"Error processing {file}: {e}")
    
    if results:
        print("\nAverage search interest for individual files:")
        for term, avg in results.items():
            print(f"  {term}: {avg:.2f}")
        most_popular = max(results, key=results.get)
        print(f"Most popular term: {most_popular} (Average: {results[most_popular]:.2f})")
    else:
        print("No valid individual file data found for analysis.")


def analyse_comparison(file_path):

    try:
        df = pd.read_csv(file_path, skiprows=1)
        if len(df.columns) < 2:
            print("CSV file does not contain enough columns for comparison.")
            return

        time_col = df.columns[0]
        df.rename(columns={time_col: 'time'}, inplace=True)
        df['time'] = pd.to_datetime(df['time'])    

        results = {}
        for col in df.columns[1:]:
            search_avg = df[col].mean()
            results[col] = search_avg

        if results:
            print("\nAverage search interest from comparison file:")
            for term, avg in results.items():
                print(f"  {term}: {avg:.2f}")
            most_popular = max(results, key=results.get)
            print(f"Most popular term: {most_popular} (Average: {results[most_popular]:.2f})")
        else:
            print("No search data columns found in the CSV.")
            
    except Exception as e:
        print(f"Error analyzing comparison file: {e}")
        
            
def analyse_files(file_downloads):

    if not file_downloads:
        print("No downloaded files available for analysis.")
        return

    if len(file_downloads) == 1:
        file = file_downloads[0]
        try:
            df = pd.read_csv(file, skiprows=1)
            if len(df.columns) > 2:
                analyse_comparison(file)
            elif len(df.columns) == 2:
                analyse_individual([file])
            else:
                print(f"File {file} does not have a recognized format for analysis.")
                
        except Exception as e:
            print(f"Error reading file {file}: {e}")

    else:
        analyse_individual(file_downloads)

            
def get_chrome_geometry(title = "Google Trends"):
    
    time.sleep(2)
    chrome_windows = gw.getWindowsWithTitle("Google Trends")

    if chrome_windows:
        chrome_win = chrome_windows[0]

        if chrome_win.isMinimized:
            chrome_win.restore()

        chrome_win.maximize()
        time.sleep(1)

        chrome_win.activate()
        c_left, c_top = chrome_win.left, chrome_win.top
        return chrome_win.left, chrome_win.top, chrome_win.width, chrome_win.height
    
    else:
        root = tk.Tk()
        c_width = root.winfo_screenwidth()
        c_height = root.winfo_screenheight()
        root.destroy()
        print(f"Chrome window not found. Using full screen: {c_width}x{c_height}")
        return 0, 0, c_width, c_height
    
def open_new_window():

    global control_panel

    for widget in control_panel.winfo_children():
        widget.destroy()

    
    control_panel.title("Content Generator")
    control_panel.geometry("700x600")

    label = tk.Label(control_panel, text="Enter your prompt:")
    label.place(relx=0.5, rely=0.4, anchor='center')

    input_entry = tk.Entry(control_panel, width=80)
    input_entry.place(relx=0.5, rely=0.5, anchor='center')
    
    # A submit button to process the input (for now, it simply prints the entered text)
    def process_input():
        user_text = input_entry.get()

    submit_button = tk.Button(control_panel, text="Submit", command=process_input)
    submit_button.place(relx=0.5, rely=0.6, anchor='center')

    
def create_control_panel(file_downloads, on_close_callback=None, width=300, height=100, position=("centre", 0)):

    placement, offset = position

    c_left, c_top, c_width, c_height = get_chrome_geometry()

    if placement == "centre":
        x_coord = c_left + (c_width - width) // 2
        y_coord = c_top + (c_height - height) // 2

    else:
        x_coord = c_left
        y_coord = c_top

    control_panel = tk.Tk()
    control_panel.title("Control Panel")
    control_panel.geometry(f"{width}x{height}+{x_coord}+{y_coord}")
    control_panel.attributes('-topmost', True)  # Bring to front
    control_panel.lift()

    button = tk.Button(control_panel, text="Analyse Downloads", command=lambda: analyse_files(file_downloads))
    button.pack(padx=10, pady=20)

    def on_close():
        if on_close_callback:
            on_close_callback()
        control_panel.destroy()
        sys.exit(0)

    control_panel.protocol("WM_DELETE_WINDOW", on_close)

    return control_panel

            
def main():
    global control_panel
    plt.ion()
    
    open_google_trends()
    
    download_thread = threading.Thread(target=process_downloads, daemon=True)
    download_thread.start()

    control_panel = create_control_panel(
        file_downloads = file_downloads,
        on_close_callback=None,
        width=300,
        height=80,
        position=("centre", 50))
    
    print("Ready for new downloads. The control panel is available on the side.")
    try:
        while True:
            try:
                file_path = download_queue.get_nowait()
                file_downloads.append(file_path)
                #visualise_data(file_path)
            except queue.Empty:
                pass
            plt.pause(0.1)
            control_panel.update_idletasks()
            control_panel.update()
            
    except KeyboardInterrupt:
        print("Exiting.")
        

if __name__ == "__main__":
    main()

