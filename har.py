import json
import sys
import csv
import os
from datetime import datetime
import re

def get_item_type(item_name):
    """
    Checks and updates a local JSON file to determine if an item is a food, nonfood, or unknown.

    Args:
        item_name (str): The name of the item.

    Returns:
        str: The type of the item ('food', 'nonfood', or 'unknown').
    """
    json_file_path = 'food_or_non_food.json'
    
    # Check if the JSON file exists and load it, otherwise start with an empty dictionary
    if os.path.exists(json_file_path):
        with open(json_file_path, 'r', encoding='utf-8') as f:
            item_data = json.load(f)
    else:
        item_data = {}

    # If the item name is in the JSON, return its type
    if item_name in item_data:
        return item_data[item_name]
    else:
        # If not, add it with 'unknown' and save the updated file
        item_data[item_name] = 'unknown'
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(item_data, f, indent=2)
        return 'unknown'

def parse_walmart_har(har_file_path, output_dir):
    """
    Parses a HAR file to extract and save Walmart order item details to a CSV.

    Args:
        har_file_path (str): The path to the .har file.
        output_dir (str): The directory where the CSV file will be created.
    """
    all_order_items = []
    order_dates = []
    
    try:
        with open(har_file_path, 'r', encoding='utf-8') as f:
            har_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: The file '{har_file_path}' was not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode the JSON from '{har_file_path}'. Is it a valid HAR file?")
        return

    print("HAR file loaded. Parsing requests for order details...")
    
    # Check if 'log' and 'entries' keys exist
    if 'log' not in har_data or 'entries' not in har_data['log']:
        print("Error: The HAR file structure is invalid. 'log' or 'entries' key is missing.")
        return

    # A recursive function to find and remove 'callFrames'
    def remove_callframes_recursive(d):
        if isinstance(d, dict):
            if 'callFrames' in d:
                del d['callFrames']
            for key, value in d.items():
                remove_callframes_recursive(value)
    
    # Iterate through all network requests (entries)
    for entry in har_data['log']['entries']:
        url = entry['request']['url']
        resource_type = entry.get('_resourceType', 'N/A')

        # Check if the URL and resource type match our criteria
        if ('/orchestra/orders/graphql/getOrder/' in url and
            resource_type in ['xhr', 'fetch']):
            print(f"Found a matching request: {url}")
            
            # Remove header and call stack information to make the file cleaner
            if 'headers' in entry['request']:
                del entry['request']['headers']
            if 'headers' in entry['response']:
                del entry['response']['headers']
            if '_initiator' in entry:
                remove_callframes_recursive(entry['_initiator'])

            try:
                # The order data is a JSON string located in the 'text' key
                response_json_text = entry['response']['content']['text']
                response_json = json.loads(response_json_text)
                
                # Navigate to the order data within the JSON
                order_data = response_json.get('data', {}).get('order', {})
                order_id = order_data.get('id')
                
                # Get the order date from the 'title' field
                order_title = order_data.get('title')

                if not order_id or not order_title:
                    print("Could not find order ID or title. Skipping this request.")
                    continue

                # Use a regular expression to extract only the date portion
                date_match = re.search(r'([A-Za-z]+\s+\d{1,2},\s+\d{4})', order_title)
                order_date = date_match.group(1) if date_match else order_title

                print(f"--> Successfully extracted data for Order ID: {order_id}")
                
                # We need to loop through the order groups to find the items
                groups = order_data.get('groups_2101', [])
                for group in groups:
                    items = group.get('items', [])
                    
                    for item in items:
                        item_name = item.get('productInfo', {}).get('name')
                        quantity = item.get('quantity')
                        price = item.get('priceInfo', {}).get('linePrice', {}).get('value')
                        
                        if item_name and quantity is not None and price is not None:
                            # Use the new function to get the item type
                            item_type = get_item_type(item_name)
                            all_order_items.append({
                                'order_id': order_id,
                                'order_date': order_date,
                                'item_name': item_name,
                                'is_food': item_type,
                                'quantity': quantity,
                                'price': price
                            })
                            print(f"----> Collected item: {item_name} (Type: {item_type})")
                
                # Add the date string to our list for filename creation
                order_dates.append(order_date)

            except (KeyError, json.JSONDecodeError) as e:
                print(f"Warning: Failed to parse data from a matching request. Error: {e}")
                continue
    
    # Check if any data was collected before trying to write the CSV
    if not all_order_items:
        print("\nNo item data was collected. The CSV file was not created.")
        return
        
    # Dynamically generate the output filename based on min/max dates
    if order_dates:
        # We need to parse the date strings to find the min and max
        # The format is now guaranteed to be 'Mon DD, YYYY'
        date_objects = [datetime.strptime(d, '%b %d, %Y') for d in order_dates]
        start_date = min(date_objects).strftime('%Y-%m-%d')
        end_date = max(date_objects).strftime('%Y-%m-%d')
        output_csv_filename = f"{start_date}_{end_date}_walmart_order_items.csv"
    else:
        output_csv_filename = "walmart_order_items.csv" # Fallback filename

    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    output_csv_path = os.path.join(output_dir, output_csv_filename)
    
    # Write the data to a CSV file
    try:
        with open(output_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['order_id', 'order_date', 'item_name', 'is_food', 'quantity', 'price']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            writer.writerows(all_order_items)
        
        print(f"\nSuccessfully saved all item data to '{output_csv_path}'.")
    except IOError as e:
        print(f"Error: Could not write to file '{output_csv_path}'. Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python har_parser.py <input_har_file.har>")
        sys.exit(1)
    
    input_har_file = sys.argv[1]
    output_dir = "output"
    parse_walmart_har(input_har_file, output_dir)
