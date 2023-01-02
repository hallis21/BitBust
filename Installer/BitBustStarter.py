# Will check for new releases on git 
# If there is a new release, it will prompt the user to update
# It will download the .zip file and extract it to the current directory
# Then it will run Bitty.exe

import json
import os
import sys
from time import sleep
import requests
import pyautogui
import zipfile


OWNER = "hallis21"
REPO = "BitBust"

# Set the API endpoint
API_ENDPOINT = f"https://api.github.com/repos/{OWNER}/{REPO}/releases/latest"

data_template = {
    'version': 'v0.0',
    'updater_version': 'v0.1',
    'latest_channel': 'sterdekie'
}


prices_template = {
    "drop_primary":  1,
    "drop_secondary":  2,
    "drop_pistol":  3,
    "drop_armor":  4,
    "drop_all_weapons":  5,
    "drop_all_wearable":  6,
    "drop_rig": 7,
    "drop_backpack": 8,
    "rotate_5_sec": 9
}



def main():
    # If "BitBustData.json" is not found, then it will create it
    # If it is found, it will check for a new release
    # The file containes the currently installed version
    
    # Prompt the user to pick between (1) Full reset (2) Check for updates and run
    opts = ["Check for updates and run", "Full reset\n(Will not reset prices)"]
    result = pyautogui.confirm(text="Welcome to BitBust!\n\nPlease select an option below", title="BitBust", \
        buttons=opts)
    
    if result is None:
        sys.exit(0)
        
    
    force_update = result == opts[1]
    
    BitBustData = data_template
    print("Checking for updates...")
    if force_update or not os.path.exists('BitBustData.json'):
        with open('BitBustData.json', 'w') as f:
            json.dump(data_template, f, indent=4)
    else:
        with open('BitBustData.json', 'r') as f:
            BitBustData = json.load(f)
    
    
    # Check if "BitBustPrices.json" exists
    # If it does not, then create it
    if not os.path.exists('BitBustPrices.json'):
        with open('BitBustPrices.json', 'w') as f:
            json.dump(prices_template, f, indent=4)
            pyautogui.alert(text="No BitBustPrices.json found. Created a new one. Please edit it and restart the script.", title="BitBust")
            sys.exit(0)
    
    
    version = ""
    try:
        response = requests.get(API_ENDPOINT)
        if response.status_code == 200:
            # Get the sha from the latest release
            version = response.json()['tag_name']
            print(f"Latest release: {version}")
        else:
            print(f"Failed to get latest release. Status code: {response.status_code}")
            sleep(10)
            sys.exit(1)
    except Exception as e:
        print(f"Fatal error getting latest release: {e}\n")
        sleep(10)
        sys.exit(1)
    
    do_update = False

    if BitBustData['version'] == "v0.0":
        print("First time running BitBustInstaller. Downloading latest version...")
        do_update = True
    elif version != BitBustData['version']:
        print("New version found!")
        opts = ["Update", "Do not update"]
        result = pyautogui.confirm(text="New version found: {}\n\nDo you want to update?".format(version), title="BitBust", buttons=["Update", "Do not update"])
        if result is None:
            sys.exit(0)
        do_update = result == opts[0]
    
    # If the version is not the same as the current version, then update
    if do_update:
        print(f"Updating to latest version:  {version}...")
        # Download the zip file
        try:
            if "BitBust.zip" in os.listdir():
                os.remove("BitBust.zip")
        except Exception as e:
            print(f"Fatal error deleting 'BitBust.zip' file: {e}\n")
            print("Please delete the file manually and try again")
            sleep(10)
            sys.exit(1)
        
        try:
            # Find asset with name "BitBust.zip"
            download_urls = response.json()['assets']
            download_url = ""
            for asset in download_urls:
                if asset['name'] == "BitBust.zip":
                    download_url = asset['browser_download_url']
                    break
            if download_url == "":
                print("Failed to find download url")
                sleep(10)
                sys.exit(1)
            print(f"Downloading zip file from: {download_url}")
            response = requests.get(download_url)
            if response.status_code == 200:
                with open('BitBust.zip', 'wb') as f:
                    f.write(response.content)
            else:
                print(f"Failed to download zip file. Status code: {response.status_code}")
                sleep(10)
                sys.exit(1)
        except Exception as e:
            print(f"Fatal error downloading zip file: {e}\n")
            sleep(10)
            sys.exit(1)
    
        # Check if the folder "BitBust" exists
        # If it does delete it
        try:
            if os.path.exists('BitBust'):
                print("Deleting old BitBust folder...")
                os.system('rmdir /S /Q BitBust')
        except Exception as e:
            print(f"Fatal error deleting old BitBust folder: {e}\n")
            print("Please delete the folder manually and try again")
            sleep(10)
            sys.exit(1)
        
        # Extract the zip file
        try:
            print("Extracting zip file...")
            with zipfile.ZipFile('BitBust.zip', 'r') as zip_ref:
                zip_ref.extractall()
        except Exception as e:
            print(f"Fatal error extracting zip file: {e}\n")
            print("Please extract the file manually and try again")
            sleep(10)
            sys.exit(1)
            
        # Delete the zip file
        try:
            os.remove('BitBust.zip')
        except Exception as e:
            print(f"Fatal error deleting zip file: {e}\n")
            print("Please delete the file manually")
            
        # Update the version in the json file
        BitBustData['version'] = version
        with open('BitBustData.json', 'w') as f:
            json.dump(BitBustData, f, indent=4)
    
    
    # Copy the prices file to the BitBust folder
    try:
        with open('BitBustPrices.json', 'r') as f:
            if os.path.exists('BitBust/prices.json'):
                os.remove('BitBust/prices.json')
            os.system('copy BitBustPrices.json BitBust/prices.json')
    except Exception as e:
        print(f"Fatal error copying prices file: {e}\n")
        print("Please copy the file manually")
        sleep(10)
        sys.exit(1)
        
        
    # Confirm with user that "latest_channel" is correct
    opts = ["Correct", "Change"]
    should_change_channel = pyautogui.confirm(text=f"Please confirm that the channel name below is correct:\n\n    '{BitBustData['latest_channel']}'",\
        title="BitBust", buttons=opts) == opts[1]
    
    if should_change_channel:
        # Prompt the user to input the channel name
        channel_name = pyautogui.prompt(text="Please enter the channel name:", title="BitBust", default=BitBustData['latest_channel'])
        # Update the json file
        BitBustData['latest_channel'] = channel_name
        with open('BitBustData.json', 'w') as f:
            json.dump(BitBustData, f, indent=4)
                
        
    # Create a file called "target_channel.txt" in the BitBust folder
    # This file will contain the channel name that the bot will join
    # Use "latest_channel" from the json file
    try:
        with open('BitBust/target_channel.txt', 'w') as f:
            f.write(BitBustData['latest_channel'])
    except Exception as e:
        print(f"Fatal error creating target_channel.txt file: {e}\n")

    print("Starting Bitty.exe...")
    sleep(2)
    # Run Bitty.exe
    try:
        os.system('start BitBust/Bitty.exe')
        print("Done!")
    except Exception as e:
        print(f"Fatal error running Bitty.exe: {e}\n")
        print("Please run the file manually")
        sleep(10)
        sys.exit(1)
            


if __name__ == '__main__':
    main()