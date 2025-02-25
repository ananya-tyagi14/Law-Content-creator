import webbrowser
import os
import time
import pandas as pd
import matplotlib.pyplot as plt
import threading
import queue

download_queue = queue.Queue()

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



def visualise_data(file_path):

    df = pd.read_csv(file_path, skiprows=1)

    print("columns in the CSV:", df.columns.tolist())

    time_col = df.columns[0]
    trend_col = df.columns[1]

    df.rename(columns={
        time_col: 'time',
        trend_col: 'search_interest'
        }, inplace=True)

    df['time'] = pd.to_datetime(df['time'])

    fig, ax = plt.subplots()

    ax.plot(df['time'], df['search_interest'], marker='o', linestyle='-')
    ax.set_xlabel('Time')
    ax.set_ylabel('Search Interest')
    ax.set_title(f'Google Trends: {trend_col}')
    ax.grid(True)
    
    fig.tight_layout()
    
    plt.show(block=False)
    plt.pause(0.1)


def process_downloads():
    downloads_folder = os.path.expanduser("~/Downloads")

    while True:
        downloaded_file = wait_for_download(downloads_folder, extension=".csv")    
        print("File has been downloaded successfully.")
        #visualise_data(downloaded_file)

        download_queue.put(downloaded_file)


def main():

    plt.ion()
    
    open_google_trends()
    
    download_thread = threading.Thread(target=process_downloads, daemon=True)
    download_thread.start()
    
    print("Ready for new downloads. Press Ctrl+C to exit.")
    try:
        while True:
            # Check if there's a new file to process and plot it in the main thread
            try:
                file_path = download_queue.get_nowait()
                visualise_data(file_path)
            except queue.Empty:
                pass
            # Allow the GUI event loop to process events
            plt.pause(0.1)
    except KeyboardInterrupt:
        print("Exiting.")
    

if __name__ == "__main__":
    main()
