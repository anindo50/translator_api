import urllib.request
import os

def download(url, file_path):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36'
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                with open(file_path, "wb") as file:
                    file.write(response.read())
                    return file_path
            else:
                # Print detailed error for debugging
                print(f"Failed to download file from URL: {url}")
                print(f"Status code: {response.status}")
                print(f"Response reason: {response.reason}")
                raise Exception(f"Failed to download file. Status code: {response.status}, Reason: {response.reason}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise
