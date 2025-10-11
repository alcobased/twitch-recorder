import streamlink
import os
from datetime import datetime
import time
import json
import sys
import logging

def setup_logging():
    """Sets up logging to a file."""
    logging.basicConfig(
        filename='recorder.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def get_config():
    """Reads and validates the configuration from config.json."""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            channel_url = config.get('channel_url')
            duration = config.get('duration', 0)
            wait_interval = config.get('wait_interval', 60)
            recording_path = config.get('recording_path')

        if not channel_url:
            logging.error("'channel_url' not found in config.json.")
            print("Error: 'channel_url' not found in config.json.")
            sys.exit(1)
            
        if not recording_path:
            logging.error("'recording_path' not found in config.json.")
            print("Error: 'recording_path' not found in config.json.")
            sys.exit(1)

        if not os.path.isabs(recording_path):
            logging.error("'recording_path' must be an absolute path.")
            print("Error: 'recording_path' must be an absolute path.")
            sys.exit(1)

        return channel_url, duration, wait_interval, recording_path
    except FileNotFoundError:
        logging.error("config.json not found.")
        print("Error: config.json not found. Please create one.")
        sys.exit(1)
    except json.JSONDecodeError:
        logging.error("Could not decode config.json.")
        print("Error: Could not decode config.json. Please ensure it is valid JSON.")
        sys.exit(1)

def get_stream(channel_url):
    """Gets the best quality stream for the given channel URL."""
    try:
        streams = streamlink.streams(channel_url)
    except streamlink.exceptions.NoPluginError:
        logging.error(f"Streamlink is unable to handle the URL: {channel_url}")
        print("Streamlink is unable to handle the URL:", channel_url)
        sys.exit(1)
    except streamlink.exceptions.PluginError as e:
        logging.error(f"Plugin error: {e}")
        print("Plugin error:", e)
        sys.exit(1)

    if not streams:
        return None

    quality = "best"
    if quality not in streams:
        logging.warning(f"Quality '{quality}' not found, defaulting to 'best'.")
        print(f"Quality '{quality}' not found, defaulting to 'best'.")
        quality = "best"
    
    return streams[quality]

def record_stream(stream, duration, recording_path):
    """Records the stream to a file."""
    fd = stream.open()
    
    if not os.path.exists(recording_path):
        os.makedirs(recording_path)
        
    now = datetime.now()
    filename = os.path.join(recording_path, f"{now.strftime('%Y-%m-%d_%H-%M-%S')}.ts")
    
    logging.info(f"Recording stream to {filename}")
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
                    logging.info(f"Recording finished after {duration} seconds.")
                    print(f"\nRecording finished after {duration} seconds.")
                    break
                
                data = fd.read(1024)
                if not data:
                    break
                f.write(data)
    except KeyboardInterrupt:
        logging.info("Recording stopped by user.")
        print("\nRecording stopped by user.")
        raise  # Re-raise the exception to exit the script
            
    finally:
        fd.close()
        logging.info("Recording finished.")
        print("Recording finished.")

def main():
    """
    Captures a Twitch live stream and saves it locally, running as a daemon.
    """
    setup_logging()
    logging.info("Script started.")
    
    channel_url, duration, wait_interval, recording_path = get_config()
    
    while True:
        stream = get_stream(channel_url)
        
        first_check = True
        while stream is None:
            if first_check:
                message = f"Stream is offline. Waiting for the stream to go live... Checking every {wait_interval} seconds."
                logging.info(message)
                print(message)
                first_check = False
            else:
                logging.info(f"Stream still offline. Waiting for {wait_interval} seconds.")

            time.sleep(wait_interval)
            stream = get_stream(channel_url)
            
        logging.info("Stream is online! Starting recorder...")
        print("Stream is online! Starting recorder...")
        try:
            record_stream(stream, duration, recording_path)
            logging.info(f"Recording finished. Waiting for {wait_interval} seconds before checking again.")
            time.sleep(wait_interval) # Wait before checking again
        except KeyboardInterrupt:
            break # Exit the while loop if Ctrl+C is pressed

    logging.info("Script finished.")

if __name__ == "__main__":
    main()
