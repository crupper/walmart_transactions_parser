import json
import sys
import csv

def parse_walmart_har(har_file_path, output_csv_path):
    """
    Parses a HAR file to extract and save Walmart order item details to a CSV.

    Args:
        har_file_path (str): The path to the .har file.
        output_csv_path (str): The path to the CSV file to be created.
    """
    all_order_items = []
    
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
                order_date = order_data.get('title')

                if not order_id:
                    print("Could not find order ID. Skipping this request.")
                    continue

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
                            all_order_items.append({
                                'order_id': order_id,
                                'order_date': order_date,
                                'item_name': item_name,
                                'quantity': quantity,
                                'price': price
                            })
                            print(f"----> Collected item: {item_name}")

            except (KeyError, json.JSONDecodeError) as e:
                print(f"Warning: Failed to parse data from a matching request. Error: {e}")
                continue
    
    # Check if any data was collected before trying to write the CSV
    if not all_order_items:
        print("\nNo item data was collected. The CSV file was not created.")
        return
        
    # Write the data to a CSV file
    try:
        with open(output_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['order_id', 'order_date', 'item_name', 'quantity', 'price']
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
    # The output CSV file path is now automatically generated
    output_csv_file = "walmart_order_items.csv"
    parse_walmart_har(input_har_file, output_csv_file)
