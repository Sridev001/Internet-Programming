// Configuration
const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:5000'; // Default to localhost for development

// Main application logic
document.addEventListener('DOMContentLoaded', () => {
    // Initialize the application
    init();
});

async function init() {
    try {
        // Load initial data
        const flights = await fetchFlights();
        displayFlights(flights);
    } catch (error) {
        console.error('Error initializing app:', error);
        showError('Failed to load application data');
    }
}

// API calls
async function fetchFlights() {
    const response = await fetch(`${API_BASE_URL}/api/flights`);
    if (!response.ok) {
        throw new Error('Failed to fetch flights');
    }
    return response.json();
}

// UI functions
function displayFlights(flights) {
    const content = document.getElementById('content');
    content.innerHTML = `
        <div class="row">
            <div class="col-12">
                <h2>Available Flights</h2>
                <div class="table-responsive">
                    <table class="table">
                        <thead>
                            <tr>
                                <th>Flight Number</th>
                                <th>From</th>
                                <th>To</th>
                                <th>Date</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${flights.map(flight => `
                                <tr>
                                    <td>${flight.flight_number}</td>
                                    <td>${flight.origin}</td>
                                    <td>${flight.destination}</td>
                                    <td>${flight.departure_time}</td>
                                    <td>
                                        <button class="btn btn-primary btn-sm" onclick="bookFlight(${flight.id})">
                                            Book Now
                                        </button>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `;
}

function showError(message) {
    const content = document.getElementById('content');
    content.innerHTML = `
        <div class="alert alert-danger" role="alert">
            ${message}
        </div>
    `;
}
