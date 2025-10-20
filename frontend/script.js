document.addEventListener("DOMContentLoaded", function() {
    const statusContainer = document.getElementById("status-container");
    const recordingsContainer = document.getElementById("recordings-container");
    const settingsForm = document.getElementById("settings-form");
    const channelsContainer = document.getElementById("channels-container");
    const addChannelButton = document.getElementById("add-channel");

    function fetchStatus() {
        fetch("/status")
            .then(response => response.json())
            .then(data => {
                let table = "<table><tr><th>Channel</th><th>Status</th><th>Last Check</th></tr>";
                for (const channel in data) {
                    const status = data[channel].status;
                    const lastCheck = data[channel].last_check;
                    table += `<tr><td>${channel}</td><td>${status}</td><td>${lastCheck || 'N/A'}</td></tr>`;
                }
                table += "</table>";
                statusContainer.innerHTML = table;
            })
            .catch(error => {
                console.error("Error fetching status:", error);
                statusContainer.innerHTML = "<p>Error fetching status.</p>";
            });
    }

    function fetchRecordings() {
        fetch("/recordings")
            .then(response => response.json())
            .then(data => {
                if (data.length === 0) {
                    recordingsContainer.innerHTML = "<p>No recordings found.</p>";
                    return;
                }

                let table = "<table><tr><th>Filename</th><th>Channel</th><th>Start Time</th><th>End Time</th></tr>";
                data.forEach(recording => {
                    table += `<tr><td>${recording.filename}</td><td>${recording.channel_url}</td><td>${recording.start_time}</td><td>${recording.end_time}</td></tr>`;
                });
                table += "</table>";
                recordingsContainer.innerHTML = table;
            })
            .catch(error => {
                console.error("Error fetching recordings:", error);
                recordingsContainer.innerHTML = "<p>Error fetching recordings.</p>";
            });
    }

    function fetchConfig() {
        fetch('/config')
            .then(response => response.json())
            .then(config => {
                document.getElementById('duration').value = config.duration;
                document.getElementById('wait_interval').value = config.wait_interval;
                document.getElementById('recording_path').value = config.recording_path;
                channelsContainer.innerHTML = '';
                config.channels.forEach((channel, index) => {
                    addChannelInput(channel.url, channel.quality);
                });
            })
            .catch(error => console.error('Error fetching config:', error));
    }

    function addChannelInput(url = '', quality = 'best') {
        const channelDiv = document.createElement('div');
        channelDiv.innerHTML = `
            <label for="channel_url">URL:</label>
            <input type="text" class="channel_url" value="${url}" required>
            <label for="channel_quality">Quality:</label>
            <input type="text" class="channel_quality" value="${quality}" required>
            <button type="button" class="remove-channel">Remove</button>
        `;
        channelsContainer.appendChild(channelDiv);
        channelDiv.querySelector('.remove-channel').addEventListener('click', () => {
            channelDiv.remove();
        });
    }

    addChannelButton.addEventListener('click', () => addChannelInput());

    settingsForm.addEventListener('submit', (event) => {
        event.preventDefault();
        const newConfig = {
            duration: parseInt(document.getElementById('duration').value, 10),
            wait_interval: parseInt(document.getElementById('wait_interval').value, 10),
            recording_path: document.getElementById('recording_path').value,
            channels: []
        };
        const channelUrlElements = document.querySelectorAll('.channel_url');
        const channelQualityElements = document.querySelectorAll('.channel_quality');
        for (let i = 0; i < channelUrlElements.length; i++) {
            newConfig.channels.push({
                url: channelUrlElements[i].value,
                quality: channelQualityElements[i].value
            });
        }

        fetch('/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(newConfig)
        })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
            fetchConfig(); // Refresh the form with the new data
        })
        .catch(error => {
            console.error('Error updating config:', error);
            alert('Error updating config.');
        });
    });

    // Initial fetches
    fetchStatus();
    fetchRecordings();
    fetchConfig();

    // Set intervals
    setInterval(fetchStatus, 10000);
    setInterval(fetchRecordings, 10000);
});
