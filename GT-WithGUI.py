import webbrowser
import os
import time


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


def main():
    
    open_google_trends()

    downloads_folder = os.path.expanduser("~/Downloads")

    downloaded_file = wait_for_download(downloads_folder, extension=".csv")

    print("file has been downloaded successfully")



if __name__ == "__main__":
    main()
