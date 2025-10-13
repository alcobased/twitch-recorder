document.addEventListener("DOMContentLoaded", function() {
    const statusContainer = document.getElementById("status-container");

    function fetchStatus() {
        fetch("/status")
            .then(response => response.json())
            .then(data => {
                const status = data.status;
                statusContainer.innerHTML = `<p>Status: ${status}</p>`;
            })
            .catch(error => {
                console.error("Error fetching status:", error);
                statusContainer.innerHTML = "<p>Error fetching status.</p>";
            });
    }

    // Fetch status on page load
    fetchStatus();

    // Fetch status every 10 seconds
    setInterval(fetchStatus, 10000);
});
