import streamlink
import os
from datetime import datetime
import time
import json
import sys
import logging
import threading
import server

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
            channels = config.get('channels')
            duration = config.get('duration', 0)
            wait_interval = config.get('wait_interval', 60)
            recording_path = config.get('recording_path')

        if not channels:
            logging.error("'channels' not found or is empty in config.json.")
            print("Error: 'channels' not found or is empty in config.json.")
            sys.exit(1)

        for channel in channels:
            if 'url' not in channel or 'quality' not in channel:
                logging.error("Each channel in 'channels' must have a 'url' and 'quality'.")
                print("Error: Each channel in 'channels' must have a 'url' and 'quality'.")
                sys.exit(1)

        if not recording_path:
            logging.error("'recording_path' not found in config.json.")
            print("Error: 'recording_path' not found in config.json.")
            sys.exit(1)

        if not os.path.isabs(recording_path):
            logging.error("'recording_path' must be an absolute path.")
            print("Error: 'recording_path' must be an absolute path.")
            sys.exit(1)

        return channels, duration, wait_interval, recording_path
    except FileNotFoundError:
        logging.error("config.json not found.")
        print("Error: config.json not found. Please create one.")
        sys.exit(1)
    except json.JSONDecodeError:
        logging.error("Could not decode config.json.")
        print("Error: Could not decode config.json. Please ensure it is valid JSON.")
        sys.exit(1)

def get_stream(channel_url, quality):
    """Gets the specified quality stream for the given channel URL."""
    try:
        streams = streamlink.streams(channel_url)
    except streamlink.exceptions.NoPluginError:
        logging.error(f"Streamlink is unable to handle the URL: {channel_url}")
        return None
    except streamlink.exceptions.PluginError as e:
        logging.error(f"Plugin error for {channel_url}: {e}")
        return None

    if not streams:
        return None

    if quality not in streams:
        logging.warning(f"Quality '{quality}' not found for {channel_url}, defaulting to 'best'.")
        quality = "best"
        if "best" not in streams:
            logging.error(f"No streams found for {channel_url}")
            return None

    return streams[quality]

def record_stream(stream, duration, recording_path, channel_url):
    """Records the stream to a file and logs the session."""
    fd = stream.open()

    if not os.path.exists(recording_path):
        os.makedirs(recording_path)

    now = datetime.now()
    channel_name = channel_url.split('/')[-1] if 'twitch.tv' in channel_url else 'stream'
    filename = os.path.join(recording_path, f"{channel_name}_{now.strftime('%Y-%m-%d_%H-%M-%S')}.ts")

    logging.info(f"Recording stream from {channel_url} to {filename}")
    print(f"Recording stream from {channel_url} to {filename}...")

    start_time_obj = datetime.now()
    start_time_iso = start_time_obj.isoformat()
    start_time = time.time()

    try:
        with open(filename, "wb") as f:
            while True:
                if duration > 0 and time.time() - start_time > duration:
                    logging.info(f"Recording finished after {duration} seconds for {channel_url}.")
                    break

                data = fd.read(1024)
                if not data:
                    break
                f.write(data)
    except KeyboardInterrupt:
        logging.info(f"Recording stopped by user for {channel_url}.")
        return

    finally:
        fd.close()
        end_time_obj = datetime.now()
        end_time_iso = end_time_obj.isoformat()

        log_entry = {
            "channel_url": channel_url,
            "filename": filename,
            "start_time": start_time_iso,
            "end_time": end_time_iso,
        }

        with open("recording_log.jsonl", "a") as log_file:
            log_file.write(json.dumps(log_entry) + "\n")

        logging.info(f"Recording finished for {channel_url}.")

def record_channel_loop(channel, duration, recording_path, wait_interval):
    """The main loop for recording a single channel."""
    channel_url = channel['url']
    quality = channel['quality']
    channel_status = server.channels_status[channel_url]
    channel_status['status'] = 'initializing'

    while True:
        channel_status['last_check'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        stream = get_stream(channel_url, quality)

        if stream is None:
            if channel_status['status'] != 'offline':
                logging.info(f"Stream for {channel_url} is offline. Waiting...")
                channel_status['status'] = 'offline'
            time.sleep(wait_interval)
            continue

        logging.info(f"Stream for {channel_url} is online! Starting recorder...")
        channel_status['status'] = 'recording'

        try:
            record_stream(stream, duration, recording_path, channel_url)
            logging.info(f"Recording for {channel_url} finished. Waiting...")
            channel_status['status'] = 'waiting'
            time.sleep(wait_interval)
        except KeyboardInterrupt:
            channel_status['status'] = 'stopped'
            break

def main():
    """
    Captures live streams and saves them locally, running as a daemon for multiple channels.
    """
    setup_logging()
    logging.info("Script started.")

    channels, duration, wait_interval, recording_path = get_config()

    for channel in channels:
        server.channels_status[channel['url']] = {'status': 'uninitialized', 'last_check': None}

    server.start_server_thread()

    threads = []
    for channel in channels:
        thread = threading.Thread(target=record_channel_loop, args=(channel, duration, recording_path, wait_interval))
        thread.daemon = True
        thread.start()
        threads.append(thread)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Shutdown signal received. Stopping all recorders.")
        print("\nShutdown signal received. Stopping all recorders.")

    logging.info("Script finished.")

if __name__ == "__main__":
    main()
