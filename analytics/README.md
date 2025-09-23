# Historical Price Analytics Dashboard

This project provides a simple way to visualize historical price data from multiple CSV files.

---

### Prerequisites

You will need to have **Python** installed on your system. The scripts use standard libraries, so no additional installations are required.

---

### Step 1: Process the Data

The first step is to run the Python script to process all the CSV files and aggregate the data into a single JSON file. This is crucial as the web page relies on this JSON file for its data.

1.  Open your **terminal** or command prompt.
2.  Navigate to the root directory of your project (`C:\Users\chris\projects\walmart_scraper`).
3.  Run the following command:
    
    `py analytics/historical_prices.py`

This will create a file named **`historical_prices_data.json`** inside the **`analytics`** directory. You should see a **"Data successfully saved to JSON"** message if it runs without errors.

---

### Step 2: Start the Web Server

A local web server is required to view the dashboard due to browser security restrictions. Python's built-in **`http.server`** is perfect for this.

1.  Ensure you are still in the project's root directory.
2.  Run the following command:
    
    `py -m http.server 8000`

This will start a local server, and you should see a message confirming that it is serving HTTP on port **8000**.

---

### Step 3: View the Dashboard

Once the server is running, you can access the interactive dashboard in your web browser.

1.  Open your web browser of choice.
2.  Navigate to the following URL:
    
    `http://localhost:8000/analytics/graph.html`

You should now see the **"Historical Price Tracker"** page with both the single-item and multi-line charts populated with your data.

---

### Testing

The `historical_prices.py` script is covered by unit tests. For more information on how to run the tests, please refer to the main `README.md` file in the project root.