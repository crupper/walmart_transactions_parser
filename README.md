# Walmart Order History Scraper

This project contains a Python script to extract your order history from a **HAR (HTTP Archive) file** and save it to a structured **CSV file**. This method is highly effective because it bypasses the website's bot detection systems by working with a static file you create by hand.

-----

### Files

  * **har\_parser.py**: This is the main script. It reads a HAR file, extracts the relevant order information, and saves it to a CSV file in the output directory.
  * **food\_or\_non\_food.json**: A JSON file that is automatically created and updated by the script. It's used to manually categorize items as **"food,"** **"nonfood,"** or **"unknown"** for your convenience.

-----

### Requirements

To run the script, you need to have **Python 3** and the following **standard libraries**, which are included with Python:

  * json
  * sys
  * csv
  * os
  * datetime
  * re

No external libraries are needed.

-----

### Step 1: Generate the HAR File

1.  Open **Google Chrome** (or another browser with Developer Tools).
2.  Navigate to the **Walmart Orders page**.
3.  Open **Developer Tools** (Ctrl + Shift + I or Cmd + Opt + I on Mac) and go to the **Network** tab.
4.  Make sure the recording button (a red circle) is active.
5.  On the Walmart website, manually **click into each order** you want to scrape. This will generate the network requests that the script needs.
6.  Once you've clicked through all the orders, right-click anywhere in the list of network requests and select **Save all as HAR with Content**. Save the file with a **.har** extension.

-----

### Step 2: Run the Script

1.  Open a terminal and navigate to the project directory.

2.  Run the **har\_parser.py** script and provide the path to your **HAR file** as an argument.

3.  Example Command:

    `py har_parser.py <path_to_your_file.har>`

-----

### Example Output:

The script will create a new directory named **`output`** (if it doesn't already exist) and save a CSV file inside it. The filename will be dynamically generated based on the start and end dates of the orders you parsed.

For example, if your orders are from September 10, 2025, and September 20, 2025, the output file will be named **`2025-09-10_2025-09-20_walmart_order_items.csv`**.

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