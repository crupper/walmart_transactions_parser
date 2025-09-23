import csv
import os
import json
from datetime import datetime

def read_csv(file_path):
    """
    Reads data from a single CSV file, handling different encodings.
    """
    data = {}
    try:
        with open(file_path, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)  # Skip the header row
            for row in reader:
                try:
                    # Unpack the row, handling potential errors
                    _, date_str, item_name, _, quantity_str, cost_str = row
                    
                    # Convert cost and quantity to float
                    cost = float(cost_str)
                    quantity = float(quantity_str)
                    
                    # Convert date string to datetime object
                    date_obj = datetime.strptime(date_str, "%b %d, %Y")
                    
                    if item_name not in data:
                        data[item_name] = []
                    data[item_name].append({
                        "date": date_obj.isoformat(),
                        "cost": cost,
                        "quantity": quantity,
                        "normalized_cost": cost / quantity if quantity else 0
                    })
                except (ValueError, IndexError) as e:
                    print(f"Skipping row due to formatting error: {row}. Error: {e}")
                    continue
    except FileNotFoundError:
        print(f"Error: The file was not found at '{file_path}'")
        return None
    except UnicodeDecodeError:
        print(f"Error: Could not decode file '{file_path}'. Please ensure it is UTF-8 encoded.")
        return None
    return data

def process_and_save_data():
    """
    Combines data from all CSV files in the 'output' directory,
    sorts it by price change, and saves it to a single JSON file.
    """
    base_dir = os.path.dirname(os.path.dirname(__file__))
    output_dir = os.path.join(base_dir, 'output')
    analytics_dir = os.path.join(base_dir, 'analytics')
    
    all_prices = {}
    
    if not os.path.exists(output_dir):
        print(f"Error: The directory '{output_dir}' was not found.")
        return

    csv_files = [f for f in os.listdir(output_dir) if f.endswith('.csv')]
    if not csv_files:
        print("No CSV files found in the 'output' directory.")
        return

    for file_name in csv_files:
        file_path = os.path.join(output_dir, file_name)
        file_data = read_csv(file_path)
        if file_data:
            for item, prices in file_data.items():
                if item not in all_prices:
                    all_prices[item] = []
                all_prices[item].extend(prices)

    # Filter out items with only one data point
    filtered_prices = {item: prices for item, prices in all_prices.items() if len(prices) > 1}

    # Sort the data for each item by date
    for item, prices in filtered_prices.items():
        filtered_prices[item] = sorted(prices, key=lambda x: x['date'])

    # Sort the items themselves based on the biggest price change
    sorted_items = sorted(filtered_prices.keys(), key=lambda item: abs(filtered_prices[item][-1]['cost'] - filtered_prices[item][0]['cost']), reverse=True)

    # Create the final sorted dictionary
    final_data = {item: filtered_prices[item] for item in sorted_items}
    
    # Save the organized data to a JSON file in the analytics directory
    output_file_path = os.path.join(analytics_dir, 'historical_prices_data.json')
    try:
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, indent=4)
        print(f"Data successfully saved to JSON at '{output_file_path}'")
    except Exception as e:
        print(f"Error saving JSON file: {e}")

if __name__ == "__main__":
    process_and_save_data()
