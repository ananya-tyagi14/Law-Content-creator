import webbrowser
import os
import time
import pandas as pd
import matplotlib.pyplot as plt


def open_google_trends():

    chrome_path = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"

    webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(chrome_path))
    
    url = "https://trends.google.com/trends/"
    
    print("Opening Google Trends...")
    webbrowser.get('chrome').open(url)


def wait_for_download(download_folder, extension=".csv"):

    print("waiting for user to download file")
    already_exists = set(os.listdir(download_folder))
    while True:
        time.sleep(1)
        current_files = set(os.listdir(download_folder))
        new_files = current_files - already_exists

        for new_file in new_files:
            if new_file.endswith(extension):
                print(f"Detected new download: {new_file}")
                return os.path.join(download_folder, new_file)

def get_new_file(download_folder):

    files = [os.path.join(download_folder, f) for f in os.listdir(download_folder)]
    files = [f for f in files if os.path.isfile(f)]
    if not files:
        return None
    return max(files, key=os.path.getmtime)


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

    search_name = trend_col

    plt.figure(figsize=(10,6))
    plt.plot(df['time'], df['search_interest'], marker='o', linestyle='-')
    plt.xlabel('Time')
    plt.ylabel('Search Interest')
    plt.title(f'Google Trends: {search_name}')
    plt.grid(True)
    plt.tight_layout()
    plt.show(block=False)
    plt.pause(0.1)


def main():
    
    open_google_trends()

    downloads_folder = os.path.expanduser("~/Downloads")

    while True:
        downloaded_file = wait_for_download(downloads_folder, extension=".csv")    
        print("File has been downloaded successfully.")
        visualise_data(downloaded_file)
    

if __name__ == "__main__":
    main()
