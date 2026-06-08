# Walmart Order History Scraper

This project contains Python scripts to extract your Walmart order history from a **HAR (HTTP Archive) file** and save it to a structured **CSV file**.

-----

### Files

  * **generate\_har.py**: Opens Walmart order history in a browser, clicks through order details, and records the network traffic to a HAR file.
  * **har\_parser.py**: Reads a HAR file, extracts the relevant order information, and saves it to a CSV file in the output directory.
  * **food\_or\_non\_food.json**: A JSON file that is automatically created and updated by the script. It's used to manually categorize items as **"food,"** **"nonfood,"** or **"unknown"** for your convenience.

-----

### Setup

Activate the project virtual environment before running the scripts:

```bash
source ./.venv/bin/activate
```

The parser uses Python standard libraries:

  * json
  * sys
  * csv
  * os
  * datetime
  * re

The browser automation dependencies are already installed in the project virtual environment.

-----

### Step 1: Generate the HAR File With Browser Automation

1.  Open a terminal and navigate to the project directory.

2.  Activate the virtual environment:

    ```bash
    source ./.venv/bin/activate
    ```

3.  Run **generate\_har.py** with an output HAR path:

    ```bash
    python generate_har.py --output inputs/<output_file>.har
    ```

4.  To collect orders from a specific date through today, pass `--end` with the earliest date to include. The date format is **MM/DD/YYYY**.

    For example, to generate a HAR for orders from a chosen start date through today:

    ```bash
    python generate_har.py --output inputs/<output_file>.har --end <MM/DD/YYYY>
    ```

5.  A browser window will open. If Walmart asks you to sign in or solve a "Robot or human?" challenge, complete it manually in the browser window. The script will continue after the order history page is available.

6.  When the automation finishes, the HAR file will be saved to the path provided with `--output`.

#### Manual HAR Option

1.  Open **Google Chrome** (or another browser with Developer Tools).
2.  Navigate to the **Walmart Orders page**.
3.  Open **Developer Tools** (Ctrl + Shift + I or Cmd + Opt + I on Mac) and go to the **Network** tab.
4.  Make sure the recording button (a red circle) is active.
5.  On the Walmart website, manually **click into each order** you want to scrape. This will generate the network requests that the script needs.
6.  Once you've clicked through all the orders, right-click anywhere in the list of network requests and select **Save all as HAR with Content**. Save the file with a **.har** extension.

-----

### Step 2: Parse the HAR File

1.  Open a terminal and navigate to the project directory.

2.  Activate the virtual environment:

    ```bash
    source ./.venv/bin/activate
    ```

3.  Run the **har\_parser.py** script and provide the path to your **HAR file** as an argument.

4.  Example Command:

    ```bash
    python har_parser.py inputs/<output_file>.har
    ```

-----

### Example Output:

The script will create a new directory named **`output`** (if it doesn't already exist) and save a CSV file inside it. The filename will be dynamically generated based on the start and end dates of the orders you parsed.

For example, if your parsed orders span `<start_date>` through `<end_date>`, the output file will be named **`<start_date>_<end_date>_walmart_order_items.csv`**.

-----

### Step 3: Categorize Items

The script will automatically create a **`food_or_non_food.json`** file. Any new items it encounters will be added to this file with an **"unknown"** value. To get the most accurate **`is_food`** column in your CSV, you can manually edit this file after your first run.

```json
{
  "Marketside Fresh Sugar Snap Peas, 8 oz": "food",
  "Marketside Fresh Sugar Snap Peas, 8 oz": "food",
  "Fresh Granny Smith Apple, Each": "food",
  "Unknown Item Name 1": "unknown"
}
```

After updating the JSON file, you can run the script again, and the **`is_food`** column will be populated with your updated values.

-----

### Testing

This project includes a suite of unit tests to ensure the scripts are working correctly. The tests are located in the `tests` directory and use Python's built-in `unittest` framework.

#### Running the Tests

To run the tests, navigate to the project root and run the following command:

```bash
python -m unittest discover tests
```

#### How the Tests Work

The tests use the `unittest.mock` library to isolate the functions from the file system. This allows the tests to run without creating or modifying any real files. The tests cover the following scenarios:

*   **`har_parser.py`**:
    *   Correctly parses a valid HAR file.
    *   Handles file not found and invalid JSON errors.
    *   Correctly identifies new and existing items in the `food_or_non_food.json` file.
*   **`analytics/historical_prices.py`**:
    *   Correctly reads and processes valid CSV files.
    *   Handles file not found and invalid CSV errors.
    *   Correctly processes multiple CSV files and creates a single JSON file.
