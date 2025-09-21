import json
import sys

def filter_har(input_har_path, output_har_path):
    """
    Filters a HAR file, keeping only requests related to Walmart order details
    and removing unnecessary headers and call stack information.

    Args:
        input_har_path (str): The path to the original, un-filtered .har file.
        output_har_path (str): The path to the new, filtered .har file.
    """
    try:
        with open(input_har_path, 'r', encoding='utf-8') as f:
            har_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: The file '{input_har_path}' was not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode the JSON from '{input_har_path}'. Is it a valid HAR file?")
        return

    print("Original HAR file loaded. Filtering requests...")

    # A new list to hold the filtered entries
    filtered_entries = []

    # Iterate through all network requests (entries)
    for entry in har_data['log']['entries']:
        url = entry['request']['url']
        resource_type = entry.get('_resourceType', 'N/A')

        # Check if the URL and resource type match our criteria
        if ('/orchestra/orders/graphql/getOrder/' in url and
            resource_type in ['xhr', 'fetch']):
            print(f"Found a matching request: {url}")
            
            # Remove header information to make the file cleaner
            if 'headers' in entry['request']:
                del entry['request']['headers']
            if 'headers' in entry['response']:
                del entry['response']['headers']
            
            # Use a recursive function to find and remove 'callFrames'
            def remove_callframes_recursive(d):
                if isinstance(d, dict):
                    if 'callFrames' in d:
                        del d['callFrames']
                    for key, value in d.items():
                        remove_callframes_recursive(value)
            
            if '_initiator' in entry:
                remove_callframes_recursive(entry['_initiator'])
            
            filtered_entries.append(entry)

    # Replace the entries with our new filtered list
    har_data['log']['entries'] = filtered_entries
    
    # Save the filtered data to a new file
    with open(output_har_path, 'w', encoding='utf-8') as f:
        json.dump(har_data, f, indent=2)

    print(f"\nFiltering complete. Saved {len(filtered_entries)} relevant requests to '{output_har_path}'.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python har_filter.py <input_har_file.har> <output_har_file.har>")
        sys.exit(1)
    
    input_har_file = sys.argv[1]
    output_har_file = sys.argv[2]
    filter_har(input_har_file, output_har_file)
