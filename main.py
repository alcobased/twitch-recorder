import streamlink
import os
from datetime import datetime
import time
import json
import sys
import logging
import threading
import server
import subprocess  # <-- NEW IMPORT


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
                logging.error(
                    "Each channel in 'channels' must have a 'url' and 'quality'.")
                print(
                    "Error: Each channel in 'channels' must have a 'url' and 'quality'.")
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
        logging.warning(
            f"Quality '{quality}' not found for {channel_url}, defaulting to 'best'.")
        quality = "best"
        if "best" not in streams:
            logging.error(f"No streams found for {channel_url}")
            return None

    return streams[quality]


def run_mkvmerge(input_filename, channel_url):
    """
    Runs mkvmerge to re-mux the .ts file into a .mkv container.
    Then, it deletes the original .ts file if successful.
    """
    # Create the output filename by replacing .ts with .mkv
    base, _ = os.path.splitext(input_filename)
    output_filename = base + ".mkv"

    # mkvmerge command: -o (output file) input_file
    command = ['mkvmerge', '-o', output_filename, input_filename]

    logging.info(f"[{channel_url}] Starting mkvmerge post-processing...")
    print(f"[{channel_url}] Starting post-processing with mkvmerge...")

    try:
        # Use subprocess.run for simple command execution
        subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True  # Raises CalledProcessError for non-zero exit codes
        )

        logging.info(
            f"[{channel_url}] mkvmerge finished successfully: {output_filename}")
        print(
            f"[{channel_url}] Post-processing successful: {os.path.basename(output_filename)}")

        # Delete the original .ts file
        os.remove(input_filename)
        logging.info(
            f"[{channel_url}] Original file deleted: {input_filename}")
        print(
            f"[{channel_url}] Original file {os.path.basename(input_filename)} deleted.")

    except subprocess.CalledProcessError as e:
        logging.error(
            f"[{channel_url}] mkvmerge failed. Exit code: {e.returncode}. Stderr: {e.stderr.strip()}")
        print(f"[{channel_url}] ERROR: mkvmerge failed. Original file retained.")

    except FileNotFoundError:
        logging.error(
            f"[{channel_url}] mkvmerge tool not found. Is it installed and in the system PATH?")
        print(
            f"[{channel_url}] ERROR: mkvmerge tool not found. Please install mkvtoolnix.")

    except Exception as e:
        logging.error(
            f"[{channel_url}] An unexpected error occurred during mkvmerge process: {e}")
        print(
            f"[{channel_url}] An unexpected error occurred during mkvmerge process: {e}")


def record_stream(stream, duration, recording_path, channel_url):
    """Records the stream to a file and logs the session."""
    fd = stream.open()

    if not os.path.exists(recording_path):
        os.makedirs(recording_path)

    now = datetime.now()
    channel_name = channel_url.split(
        '/')[-1] if 'twitch.tv' in channel_url else 'stream'

    # NOTE: We temporarily use .ts as the container for the raw stream data
    temp_filename = os.path.join(
        recording_path, f"{channel_name}_{now.strftime('%Y-%m-%d_%H-%M-%S')}.ts")

    logging.info(f"Recording stream from {channel_url} to {temp_filename}")
    print(f"Recording stream from {channel_url} to {temp_filename}...")

    start_time_obj = datetime.now()
    start_time_iso = start_time_obj.isoformat()
    start_time = time.time()

    is_successful_record = False  # Flag to track if we should run mkvmerge/log

    try:
        with open(temp_filename, "wb") as f:
            while True:
                if duration > 0 and time.time() - start_time > duration:
                    logging.info(
                        f"Recording finished after {duration} seconds for {channel_url}.")
                    is_successful_record = True
                    break

                data = fd.read(1024)
                if not data:
                    is_successful_record = True  # Stream ended naturally
                    break
                f.write(data)
    except KeyboardInterrupt:
        logging.info(f"Recording stopped by user for {channel_url}.")
        # Do not log or process if stopped by user
        return

    finally:
        fd.close()
        logging.info(f"Recording stream file closed for {channel_url}.")

        if is_successful_record and os.path.exists(temp_filename):
            # 1. Run mkvmerge and delete the .ts file
            run_mkvmerge(temp_filename, channel_url)

            # 2. Log the session (using the final .mkv filename)
            end_time_obj = datetime.now()
            end_time_iso = end_time_obj.isoformat()

            # The final filename will be the one created by mkvmerge (base + .mkv)
            base, _ = os.path.splitext(temp_filename)
            final_filename = base + ".mkv"

            log_entry = {
                "channel_url": channel_url,
                "filename": final_filename,
                "start_time": start_time_iso,
                "end_time": end_time_iso,
            }

            with open("recording_log.jsonl", "a") as log_file:
                log_file.write(json.dumps(log_entry) + "\n")

            logging.info(f"Recording finished and logged for {channel_url}.")
        else:
            logging.warning(
                f"Recording interrupted or file missing for {channel_url}. Skipping post-processing and logging.")
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
                logging.info(f"Removed partial file {temp_filename}.")


def record_channel_loop(channel, duration, recording_path, wait_interval):
    """The main loop for recording a single channel."""
    channel_url = channel['url']
    quality = channel['quality']
    # Use the base channel name for console output clarity
    channel_name = channel_url.split(
        '/')[-1] if 'twitch.tv' in channel_url else 'stream'

    server.channels_status[channel_url] = server.channels_status.get(
        channel_url, {'status': 'initializing', 'last_check': None})
    channel_status = server.channels_status[channel_url]
    channel_status['status'] = 'initializing'
    channel_status['name'] = channel_name  # Add name for easier reading

    while True:
        channel_status['last_check'] = datetime.now().strftime(
            '%Y-%m-%d %H:%M:%S')
        stream = get_stream(channel_url, quality)

        if stream is None:
            if channel_status['status'] != 'offline':
                logging.info(
                    f"[{channel_name}] Stream is offline. Waiting...")
                channel_status['status'] = 'offline'
            time.sleep(wait_interval)
            continue

        logging.info(
            f"[{channel_name}] Stream is online! Starting recorder...")
        channel_status['status'] = 'recording'
        channel_status['recording_since'] = datetime.now().strftime(
            '%Y-%m-%d %H:%M:%S')

        try:
            record_stream(stream, duration, recording_path, channel_url)

            # The recording finished successfully (by duration or stream end)
            logging.info(f"[{channel_name}] Recording finished. Waiting...")
            channel_status['status'] = 'waiting'
            channel_status.pop('recording_since', None)
            time.sleep(wait_interval)

        except KeyboardInterrupt:
            channel_status['status'] = 'stopped'
            channel_status.pop('recording_since', None)
            break


def main():
    """
    Captures live streams and saves them locally, running as a daemon for multiple channels.
    """
    setup_logging()
    logging.info("Script started.")

    try:
        channels, duration, wait_interval, recording_path = get_config()
    except SystemExit:
        return

    for channel in channels:
        # Note: The channel status should ideally be cleared/re-initialized here
        # to ensure server doesn't hold stale data if config changed.
        server.channels_status[channel['url']] = {
            'status': 'uninitialized', 'last_check': None}

    # Start the HTTP server thread
    server.start_server_thread()

    threads = []
    for channel in channels:
        thread = threading.Thread(target=record_channel_loop, args=(
            channel, duration, recording_path, wait_interval))
        thread.daemon = True
        thread.start()
        threads.append(thread)

    try:
        # Keep the main thread alive while worker threads and server thread run
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Shutdown signal received. Stopping all recorders.")
        print("\nShutdown signal received. Stopping all recorders.")

        # --- NEW GRACEFUL SHUTDOWN ---
        # Stop the web server before the main process exits
        server.stop_server()

    logging.info("Script finished.")


if __name__ == "__main__":
    main()
