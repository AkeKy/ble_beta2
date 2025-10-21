> [!NOTE]
> This guide provides step-by-step instructions for setting up and running the BLE Indoor Positioning System on your local machine. Please follow each step carefully.

# User Guide: BLE Indoor Positioning System

Welcome to the BLE Indoor Positioning System. This guide will walk you through the entire process, from installation to real-time tracking.

## Table of Contents

1.  [Prerequisites](#1-prerequisites)
2.  [Installation](#2-installation)
3.  [Running the Backend Server](#3-running-the-backend-server)
4.  [Step 1: Gateway Registration](#4-step-1-gateway-registration)
5.  [Step 2: Real-time Tracking](#5-step-2-real-time-tracking)
6.  [Step 3: Viewing Statistics](#6-step-3-viewing-statistics)
7.  [Troubleshooting](#7-troubleshooting)

---

## 1. Prerequisites

Before you begin, ensure you have the following:

*   **Python 3.11 or newer**: You can download it from [python.org](https://www.python.org/downloads/).
*   **University Network Connection**: You MUST be connected to your university's network (either via WiFi or VPN) to access the EazyTrax server at `http://10.101.119.12:8001`.
*   **BLE Tag**: The target BLE tag (`C4D36AD87176`) must be powered on and within range of the university's gateways.
*   **Web Browser**: A modern web browser like Chrome, Firefox, or Edge.

---

## 2. Installation

This step involves setting up the necessary Python libraries for the backend server.

1.  **Unzip the Project**: Unzip the `ble-trilateration.zip` file to a location of your choice on your computer.

2.  **Open a Terminal/Command Prompt**: Navigate into the project's `backend` directory.
    ```bash
    cd path/to/ble-trilateration/backend
    ```

3.  **Install Dependencies**: Run the following command to install all required Python packages.
    ```bash
    pip install -r requirements.txt
    ```
    This will install Flask, Flask-SocketIO, requests, and other necessary libraries.

---

## 3. Running the Backend Server

The backend server is the heart of the system. It handles data scraping, position calculations, and communication with the frontend.

*   **Start the Server**: While still in the `backend` directory, run the following command:
    ```bash
    python app.py
    ```

*   **Verify**: You should see output indicating the server is running, similar to this:
    ```
    INFO:__main__:Starting BLE Trilateration Server...
    INFO:werkzeug: * Running on http://127.0.0.1:5000
    (Press CTRL+C to quit)
    ```

> [!IMPORTANT]
> Keep this terminal window open. Closing it will stop the backend server.

---

## 4. Step 1: Gateway Registration

Before you can track the tag, you must tell the system where the gateways are located. **This is the most critical step for accuracy.**

1.  **Open the Registration Page**: Open your web browser and navigate to:
    **[http://localhost:5000/gateway_registration.html](http://localhost:5000/gateway_registration.html)**

2.  **Load Floor Plan**: Make sure your floor plan images (e.g., `floor5.png`) are placed in the `frontend/images/` directory. The page will automatically try to load the image for the selected floor.

3.  **Register Each Gateway**:
    *   Select the correct **floor** from the dropdown menu.
    *   **Click** on the map at the exact location of a gateway.
    *   A popup will appear. Enter the **MAC Address** of the gateway (e.g., `9C:8C:D8:C7:E0:16`).
    *   Click **"Save Gateway"**.
    *   A green marker for the gateway will appear on the map.

4.  **Repeat**: Repeat this process for **at least 3 gateways** on the floor you want to track. For best results, register as many gateways as possible (10-20 is recommended) and ensure they are spread out across the area.

---

## 5. Step 2: Real-time Tracking

Once gateways are registered, you can start tracking the BLE tag.

1.  **Open the Tracking Page**: In your browser, go to:
    **[http://localhost:5000/tracking.html](http://localhost:5000/tracking.html)**

2.  **Select Floor**: Choose the floor you want to track from the dropdown menu.

3.  **Start Tracking**: Click the **"Start Tracking"** button.

4.  **View Position**: The system will now:
    *   Fetch data from the EazyTrax API.
    *   Calculate the tag's position.
    *   Display a red marker on the map representing the tag's location.
    *   The sidebar will show the detected gateways and their signal strengths.

The position will update automatically every few seconds.

---

## 6. Step 3: Viewing Statistics

The system stores all calculated positions in the database. You can view historical data and analytics on the statistics page.

1.  **Open the Statistics Page**: In your browser, go to:
    **[http://localhost:5000/statistics.html](http://localhost:5000/statistics.html)**

2.  **Analyze Data**: This page provides:
    *   **Summary Cards**: Total positions, average accuracy, etc.
    *   **Charts**: Position timeline, gateway signal distribution, and more.
    *   **Heatmap**: A visual representation of where the tag has spent the most time.
    *   **History Table**: A paginated log of all recorded positions.

Use the filters at the top to narrow down the data by floor and time range.

---

## 7. Troubleshooting

*   **Problem**: "Failed to fetch API data" or the scraper shows 0 gateways.
    *   **Solution**: Ensure you are connected to your university's network. The EazyTrax server is not accessible from the public internet.

*   **Problem**: "Not enough gateways" error during tracking.
    *   **Solution**: You need at least 3 gateways to be actively detecting the tag *and* registered in the system for the selected floor. Go back to the Gateway Registration page and add more gateways.

*   **Problem**: The position is inaccurate or jumps around.
    *   **Solution**: This is common with RSSI-based positioning. To improve accuracy:
        *   Register more gateways.
        *   Ensure the gateway positions you registered are accurate.
        *   The Kalman filter is already implemented to help smooth the position, but a strong base of gateway data is essential.

