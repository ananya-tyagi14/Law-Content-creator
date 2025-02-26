import webbrowser
import os
import time
import pandas as pd
import matplotlib.pyplot as plt
import threading
import queue

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
                file_downloads.append(file_path)
                visualise_data(file_path)
            except queue.Empty:
                pass
            # Allow the GUI event loop to process events
            plt.pause(0.1)
            
    except KeyboardInterrupt:
        print("Exiting.")
        analyse_files(file_downloads)
        

if __name__ == "__main__":
    main()

