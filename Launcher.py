import requests
import json
import os

Github = "https://raw.githubusercontent.com/RebornEnder/screenblox/main/"
DataPath = os.environ['USERPROFILE'] + "\\ScreenshareData"
Version = f"{DataPath}\\Version.json"
AppPath = f"{DataPath}\\App.py"

def main():
    print("Screenshare Launcher")
    print("[~] Checking for updates...")
    try:
        newversion = requests.get(Github + "Data/Version.json")
        if not os.path.exists(DataPath):
            print("[+] First launch detected, downloading files...")
            os.mkdir(DataPath)
            newapp = requests.get(Github + "Data/App.py")
            with open(AppPath, mode="xb") as file:
                file.write(newapp.content)
            with open(Version, mode="xb") as file:
                file.write(newversion.content)
            print("[+] Launching...\n")
            os.system(f"python {AppPath}")
        elif newversion.json()["Version"] < json.load(open(Version))["Version"] + 0.1:
            print("[+] Up to date, launching...\n")
            os.system(f"python {AppPath}")
        else:
            print("[-] Out of date, updating...")
            newapp = requests.get(Github + "Data/App.py")
            with open(AppPath, mode="wb") as file:
                file.write(newapp.content)
            with open(Version, mode="wb") as file:
                file.write(newversion.content)
            print("[+] Launching...\n")
            os.system(f"python {AppPath}")
    except Exception as e:
        print("[-] Update checking/downloading failed!\n", e)
        os.system(f"python {AppPath}")

if __name__ == "__main__":
    main()