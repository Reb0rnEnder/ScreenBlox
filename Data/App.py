from flask import Flask, Response, request
from gevent.pywsgi import WSGIServer
from PIL import Image, ImageGrab
import os
import os
import cv2
import json
import requests
import subprocess
import pydirectinput

app = Flask(__name__)

# Configuration
config = {
    "robloxpath": "",
    "video_path": "",
    "video_processed": "",
    "video_mode": False,
    "keyboard": False,
    "mouse": False,
    "roblox": False,
    "resx": 190,
    "resy": 90
}

# Config file
config_file = "Config.json"

# Pre-process and store video frames
video_frames_hex = []

# Set needed variables for video settings
video_lenght = 0

# Whitelisted Keys
valid_keys = {"w", "a", "s", "d", "i", "o", "left", "right", "space"}

def findroblox():
    versions = os.path.join(os.getenv("LOCALAPPDATA"), "Roblox", "Versions") 
    if not os.path.exists(versions):
        return ""    
    for version in os.listdir(versions):
        exe = os.path.join(versions, version, "RobloxPlayerBeta.exe")      
        if os.path.exists(exe):
            return exe
    return ""

def load_config():
    global config
    if os.path.exists(config_file) and os.path.getsize(config_file) > 0:
        with open(config_file, "r") as f:
            config = json.load(f)
    else:
        save_config()

def save_config():
    with open(config_file, "w") as f:
        json.dump(config, f, indent=4)

def edit_config():
    edit_prompt = input("[?] Do you want to edit the configuration? (y/n): ").lower()
    if edit_prompt == "y":
        for key in config.keys():
            new_value = input(f"[~] Enter value for {key} (current: {config[key]}): ")
            if new_value.lower() == "true":
                config[key] = True
            elif new_value.lower() == "false":
                config[key] = False
            elif isinstance(new_value, int):
                config[key] = int(new_value)
            elif new_value:
                config[key] = new_value
        save_config()

def save_hex_to_file(hex_data, video_path):
    save_prompt = input("Do you want to save the processed frames to a text file? (y/n): ").lower()
    if save_prompt == 'y':
        text_file_name = video_path.rsplit('.', 1)[0] + '.videotxt'
        with open(text_file_name, 'w') as file:
            for hex_str in hex_data:
                file.write(f"{hex_str}\n")
        print(f"Frames saved to {text_file_name}")
    else:
        print("Frames were not saved.")


def adjust_fps_to_60(frame, target_fps, current_fps):
    if current_fps > target_fps:
        skip_rate = round(current_fps / target_fps)
        return [frame] if frame % skip_rate == 0 else []
    elif current_fps < target_fps:
        duplicate_rate = round(target_fps / current_fps)
        return [frame] * duplicate_rate
    else:
        return [frame]

def process_video_hex():
    cap = cv2.VideoCapture(config["video_path"])
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    vid_fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_counter = 0
    adjusted_frames_counter = 0
    
    while True:
        success, frame = cap.read()
        if not success:
            break
        for _ in adjust_fps_to_60(frame_counter, 60, vid_fps):
            frame = cv2.resize(frame, (config["resx"], config["resy"]))
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            hex_str = ','.join([f'"{r:02x}{g:02x}{b:02x}"' for r, g, b in rgb_frame.reshape(-1, 3)])
            video_frames_hex.append(hex_str)
            adjusted_frames_counter += 1
            print(f'[+] Frames Adjusted & Processed: {adjusted_frames_counter}/{total_frames}', end='\r')

        frame_counter += 1

    print(f'\n[+] All frames processed and adjusted to 60 FPS: {adjusted_frames_counter}/{total_frames}.')
    cap.release()
    return len(video_frames_hex) - 1

def generate_rgb():
    screenshot = ImageGrab.grab().resize((config["resx"], config["resy"]))
    rgb_str = ','.join([f'"{r},{g},{b}"' for r, g, b in screenshot.getdata()])
    return f'{{"RGB": [{rgb_str}]}}'

def generate_hex():
    screenshot = ImageGrab.grab().resize((config["resx"], config["resy"]))
    hex_str = ','.join([f'"{r:02x}{g:02x}{b:02x}"' for r, g, b in screenshot.getdata()])
    return f'{{"HEX": [{hex_str}]}}'

if config["video_mode"]:
    @app.route('/')
    def index():
        frame_index = request.args.get('frame', default=0, type=int)
        if frame_index < len(video_frames_hex):
            return Response(f'{{"HEX": [{video_frames_hex[frame_index]}]}}', mimetype = 'application/json')
        else:
            return Response('{"Error": "Frame index out of range"}', mimetype = 'application/json', status = 404)
else:
    @app.route('/')
    def index():
        return Response(generate_hex(), mimetype='application/json')
    
@app.route('/vidsett')
def video_settings():
    if config["video_mode"]:
        return {"LEN": [video_lenght, 60]}
    else:
        return {"LEN": [0, 0]}

@app.route('/res')
def resolution():
    return {"RES": [config["resx"], config["resy"]]}

@app.route('/key')
def keyboard_status():
    return {"KEY": config["keyboard"]}

@app.route('/keysend')
def keyboard_type():
    key = request.args.get('key', '', type=str).lower()
    if config["keyboard"] and key in valid_keys:
        pydirectinput.press(key)
        return {"KEYSEND": True}
    return {"KEYSEND": False}

@app.route('/mousclick')
def mouse_click():
    x, y, btn = request.args.get('x', 0, type=int), request.args.get('y', 0, type=int), request.args.get('btn', 0, type=str)
    if config["mouse"]:
        pydirectinput.click(x, y, button=btn)
        return {"MOUSECLICK": True}
    return {"MOUSECLICK": False}

@app.route('/roblox')
def roblox_status():
    return {"ROBLOX": config["roblox"]}

@app.route('/robloxjoin')
def roblox_join():
    placeid = request.args.get('placeid')
    if config["roblox"] and placeid:
        subprocess.run(["taskkill", "/f", "/im", "RobloxPlayerBeta.exe"], check=False)
        subprocess.run([config["robloxpath"], f"roblox://placeID={placeid}"], check=False)
        return {"ROBLOXJOIN": True}
    return {"ROBLOXJOIN": False}

if __name__ == '__main__':
    os.system("title Screenshare Encoder / Made by @RebornEnder (zdir)")

    load_config()
    edit_config()

    if config["robloxpath"] == "" and config["roblox"]:
        config["robloxpath"] = findroblox()

    if config["video_mode"] and config["video_processed"] and os.path.exists(config["video_processed"]):
        with open(config["video_processed"], 'r') as file:
            video_frames_hex = [line.strip() for line in file.readlines()]
        print(f"Loaded frames from {config['video_processed']}")
        video_lenght = len(video_frames_hex) - 1
    elif config["video_mode"]:
        video_lenght = process_video_hex()
        save_hex_to_file(video_frames_hex, config["video_path"])

    print(f'[+] Output Resolution: {config["resx"]}x{config["resy"]}.')
    print(f'[+] Keyboard Status: {str(config["keyboard"])}.')
    print(f'[+] Mouse Status: {str(config["mouse"])}.')
    print(f'[+] Roblox GameJoin Status: {str(config["roblox"])}.')
    print(f'[+] Roblox Executable Path: {config["robloxpath"]}.')
    print(f'[+] Hosting Server On: http://127.0.0.1:8080.\n')
    server = WSGIServer(('127.0.0.1', 8080), app)
    server.serve_forever()
