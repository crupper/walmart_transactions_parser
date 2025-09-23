
import unittest
import os
import csv
from unittest.mock import patch, mock_open
from har_parser import parse_walmart_har

import json

class TestParseWalmartHar(unittest.TestCase):

    def setUp(self):
        self.output_dir = "test_output"
        self.har_dir = "test_hars"
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.har_dir, exist_ok=True)
        
        har_data = {
            "log": {
                "entries": [
                    {
                        "_resourceType": "xhr",
                        "request": {
                            "url": "https://www.walmart.com/orchestra/orders/graphql/getOrder/12345"
                        },
                        "response": {
                            "content": {
                                "text": json.dumps({
                                    "data": {
                                        "order": {
                                            "id": "12345",
                                            "title": "Order delivered on Jan 1, 2024",
                                            "groups_2101": [
                                                {
                                                    "items": [
                                                        {
                                                            "productInfo": {"name": "Test Item"},
                                                            "quantity": 1,
                                                            "priceInfo": {"linePrice": {"value": "10.00"}}
                                                        },
                                                        {
                                                            "productInfo": {"name": "Another Item"},
                                                            "quantity": 2,
                                                            "priceInfo": {"linePrice": {"value": "5.00"}}
                                                        }
                                                    ]
                                                }
                                            ]
                                        }
                                    }
                                })
                            }
                        }
                    }
                ]
            }
        }
        
        self.har_file_path = os.path.join(self.har_dir, "sample.har")
        with open(self.har_file_path, 'w') as f:
            json.dump(har_data, f)

    def tearDown(self):
        for f in os.listdir(self.output_dir):
            os.remove(os.path.join(self.output_dir, f))
        os.rmdir(self.output_dir)
        
        for f in os.listdir(self.har_dir):
            os.remove(os.path.join(self.har_dir, f))
        os.rmdir(self.har_dir)

    @patch("har_parser.get_item_type", return_value="unknown")
    def test_parse_walmart_har_valid_file(self, mock_get_item_type):
        """Test that a valid HAR file is parsed correctly."""
        parse_walmart_har(self.har_file_path, self.output_dir)

        # Check that the CSV file was created
        output_files = os.listdir(self.output_dir)
        self.assertEqual(len(output_files), 1)
        
        output_csv_path = os.path.join(self.output_dir, output_files[0])
        with open(output_csv_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]['item_name'], "Test Item")
            self.assertEqual(rows[1]['item_name'], "Another Item")

    @patch("builtins.print")
    def test_parse_walmart_har_file_not_found(self, mock_print):
        """Test that a FileNotFoundError is handled."""
        parse_walmart_har("non_existent_file.har", self.output_dir)
        mock_print.assert_called_with("Error: The file 'non_existent_file.har' was not found.")

    @patch("builtins.print")
    @patch("builtins.open", new_callable=mock_open, read_data="invalid json")
    def test_parse_walmart_har_invalid_json(self, mock_file, mock_print):
        """Test that a JSONDecodeError is handled."""
        parse_walmart_har("any_file.har", self.output_dir)
        mock_print.assert_called_with("Error: Could not decode the JSON from 'any_file.har'. Is it a valid HAR file?")

    @patch("builtins.print")
    @patch("builtins.open", new_callable=mock_open, read_data="{\"log\": {}}")
    def test_parse_walmart_har_missing_entries_key(self, mock_file, mock_print):
        """Test that a missing 'entries' key is handled."""
        parse_walmart_har("any_file.har", self.output_dir)
        mock_print.assert_called_with("Error: The HAR file structure is invalid. 'log' or 'entries' key is missing.")

if __name__ == "__main__":
    unittest.main()
