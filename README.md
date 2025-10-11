# Twitch Stream Recorder

This is a simple Python script to record Twitch live streams using `streamlink`.

## Running

To run the script, use the following command:

```bash
uv run main.py
```

The script will look for a `config.json` file in the same directory.

## Configuration

You need to create a `config.json` file to specify the channel URL and recording duration. An example is provided in `config.example.json`.

1.  Create a file named `config.json`.
2.  Add the following content to the file, replacing the placeholder values with your desired settings:

    ```json
    {
        "channel_url": "<your_twitch_channel_url>",
        "duration": 0,
        "wait_interval": 60,
        "recording_path": "/path/to/your/recordings"
    }
    ```

*   `channel_url`: The URL of the Twitch channel you want to record.
*   `duration`: The duration of the recording in seconds. If set to `0`, the recording will continue until the broadcast ends or is manually interrupted (e.g., by pressing `Ctrl+C`).
*   `wait_interval`: The interval in seconds to wait before checking if the stream is online again. Defaults to 60 seconds if not provided.
*   `recording_path`: The absolute path to the directory where recordings will be stored.

## Add dependencies

To add new dependencies, use the `uv add` command:

```bash
uv add <dependency_name>
```
