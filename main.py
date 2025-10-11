import streamlink
import os
from datetime import datetime
import time
import json
import sys

def main():
    """
    Captures a Twitch live stream and saves it locally.
    """
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            channel_url = config.get('channel_url')
            duration = config.get('duration', 0)
        if not channel_url:
            print("Error: 'channel_url' not found in config.json.")
            sys.exit(1)
    except FileNotFoundError:
        print("Error: config.json not found. Please create one.")
        sys.exit(1)
    except json.JSONDecodeError:
        print("Error: Could not decode config.json. Please ensure it is valid JSON.")
        sys.exit(1)

    try:
        streams = streamlink.streams(channel_url)
    except streamlink.exceptions.NoPluginError:
        print("Streamlink is unable to handle the URL:", channel_url)
        sys.exit(1)
    except streamlink.exceptions.PluginError as e:
        print("Plugin error:", e)
        sys.exit(1)

    if not streams:
        print("No streams found on the given URL.")
        sys.exit(1)

    quality = "best"
    if quality not in streams:
        print(f"Quality '{quality}' not found, defaulting to 'best'.")
        quality = "best"
    
    stream = streams[quality]
    
    fd = stream.open()
    
    if not os.path.exists("recordings"):
        os.makedirs("recordings")
        
    now = datetime.now()
    filename = f"recordings/{now.strftime('%Y-%m-%d_%H-%M-%S')}.ts"
    
    print(f"Recording stream to {filename}...")
    if duration > 0:
        print(f"Recording will stop automatically after {duration} seconds.")
    else:
        print("Recording until the broadcast ends or you press Ctrl+C to stop.")
    print("Press Ctrl+C to stop recording.")
    
    start_time = time.time()
    
    try:
        with open(filename, "wb") as f:
            while True:
                if duration > 0 and time.time() - start_time > duration:
                    print(f"\nRecording finished after {duration} seconds.")
                    break
                
                data = fd.read(1024)
                if not data:
                    break
                f.write(data)
    except KeyboardInterrupt:
        print("\nRecording stopped by user.")
            
    finally:
        fd.close()
        print("Recording finished.")

if __name__ == "__main__":
    main()