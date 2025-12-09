# LAE-GPT Dashboard

This is a web-based dashboard for the LAE-GPT Flight Dispatcher system. It visualizes the automated approval process, including mission details, regulation retrieval, physics checks, and final AI decisions.

## Prerequisites

- Python 3.9+
- The parent `LAE-GPT` project must be populated with scenarios and reports.

## Installation

1. Navigate to this directory:
   ```bash
   cd web_dashboard
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Dashboard

1. Start the backend server:
   ```bash
   python3 app.py
   ```

2. Open your browser and go to:
   `http://localhost:8000`

## Features

- **Scenario Browser**: Browse all available flight scenarios (S001-S049).
- **Mission Details**: View aircraft, waypoints, and mission parameters.
- **Playback Mode**: Simulate the AI's decision-making process (Regulations -> Physics -> Reasoning).
- **Verification**: Compare the AI's output against the Ground Truth data.
