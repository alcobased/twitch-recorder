
# Twitch Stream Recorder

This is a simple Python script to record Twitch live streams using `streamlink`.

## Running

There are two ways to run this script:

**1. Using command-line arguments:**

```bash
uv run main.py <twitch_channel_url> [duration_in_seconds]
```

*   `<twitch_channel_url>`: The URL of the Twitch channel you want to record.
*   `[duration_in_seconds]`: (Optional) The duration of the recording in seconds.

**2. Using a configuration file:**

If you run the script without any arguments, it will look for a `config.json` file in the same directory.

```bash
uv run main.py
```

## Configuration

You can create a `config.json` file to specify the channel URL. This is useful if you frequently record the same channel.

1.  Create a file named `config.json`.
2.  Add the following content to the file, replacing `<your_twitch_channel_url>` with the actual channel URL:

    ```json
    {
        "channel_url": "<your_twitch_channel_url>"
    }
    ```

    An example is provided in `config.example.json`.

## Add dependencies

To add new dependencies, use the `uv add` command:

```bash
uv add <dependency_name>
```
