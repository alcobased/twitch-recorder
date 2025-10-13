document.addEventListener("DOMContentLoaded", function() {
    const statusContainer = document.getElementById("status-container");
    const recordingsContainer = document.getElementById("recordings-container");

    function fetchStatus() {
        fetch("/status")
            .then(response => response.json())
            .then(data => {
                const status = data.status;
                const lastCheck = data.last_check;
                statusContainer.innerHTML = `<p>Status: ${status}</p><p>Last Check: ${lastCheck}</p>`;
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

                let table = "<table><tr><th>Filename</th><th>Start Time</th><th>End Time</th></tr>";
                data.forEach(recording => {
                    table += `<tr><td>${recording.filename}</td><td>${recording.start_time}</td><td>${recording.end_time}</td></tr>`;
                });
                table += "</table>";
                recordingsContainer.innerHTML = table;
            })
            .catch(error => {
                console.error("Error fetching recordings:", error);
                recordingsContainer.innerHTML = "<p>Error fetching recordings.</p>";
            });
    }

    // Fetch status and recordings on page load
    fetchStatus();
    fetchRecordings();

    // Fetch status and recordings every 10 seconds
    setInterval(fetchStatus, 10000);
    setInterval(fetchRecordings, 10000);
});