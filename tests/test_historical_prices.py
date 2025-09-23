
import unittest
import os
import sys
import csv
import json
from datetime import datetime
from unittest.mock import patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from analytics.historical_prices import read_csv, process_and_save_data

class TestProcessAndSaveData(unittest.TestCase):

    def setUp(self):
        self.output_dir = "output"
        self.analytics_dir = "analytics"
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.analytics_dir, exist_ok=True)

    def tearDown(self):
        if os.path.exists(self.output_dir):
            for f in os.listdir(self.output_dir):
                os.remove(os.path.join(self.output_dir, f))
            os.rmdir(self.output_dir)
        
        json_file_path = os.path.join(self.analytics_dir, "historical_prices_data.json")
        if os.path.exists(json_file_path):
            os.remove(json_file_path)

    @patch("builtins.print")
    def test_process_and_save_data_no_csv_files(self, mock_print):
        """Test that no CSV files are found."""
        process_and_save_data()
        mock_print.assert_any_call("No CSV files found in the 'output' directory.")

    def test_process_and_save_data_valid_csv_files(self):
        """Test that valid CSV files are processed correctly."""
        # Create some sample CSV files
        with open(os.path.join(self.output_dir, "sample1.csv"), 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["order_id", "order_date", "item_name", "is_food", "quantity", "price"])
            writer.writerow(["12345", "Jan 01, 2024", "Test Item", "unknown", "1", "10.00"])
        
        with open(os.path.join(self.output_dir, "sample2.csv"), 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["order_id", "order_date", "item_name", "is_food", "quantity", "price"])
            writer.writerow(["12345", "Jan 02, 2024", "Test Item", "unknown", "1", "12.00"])

        process_and_save_data()

        # Check that the JSON file was created
        json_file_path = os.path.join(self.analytics_dir, "historical_prices_data.json")
        self.assertTrue(os.path.exists(json_file_path))

        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertIn("Test Item", data)
            self.assertEqual(len(data["Test Item"]), 2)
            self.assertEqual(data["Test Item"][0]["cost"], 10.00)
            self.assertEqual(data["Test Item"][1]["cost"], 12.00)

    @patch("builtins.print")
    def test_process_and_save_data_output_dir_not_found(self, mock_print):
        """Test that the output directory not found is handled."""
        # Temporarily rename the output directory
        os.rename(self.output_dir, "output_temp")
        process_and_save_data()
        # Rename it back
        os.rename("output_temp", self.output_dir)
        mock_print.assert_any_call(f"Error: The directory '{os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), self.output_dir)}' was not found.")


class TestReadCsv(unittest.TestCase):

    def setUp(self):
        self.csv_dir = "test_csvs"
        os.makedirs(self.csv_dir, exist_ok=True)
        self.sample_csv_path = os.path.join(self.csv_dir, "sample.csv")
        with open(self.sample_csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["order_id", "order_date", "item_name", "is_food", "quantity", "price"])
            writer.writerow(["12345", "Jan 01, 2024", "Test Item", "unknown", "1", "10.00"])
            writer.writerow(["12345", "Jan 01, 2024", "Another Item", "unknown", "2", "5.00"])

    def tearDown(self):
        for f in os.listdir(self.csv_dir):
            os.remove(os.path.join(self.csv_dir, f))
        os.rmdir(self.csv_dir)

    def test_read_csv_valid_file(self):
        """Test that a valid CSV file is parsed correctly."""
        data = read_csv(self.sample_csv_path)
        self.assertIn("Test Item", data)
        self.assertEqual(len(data["Test Item"]), 1)
        self.assertEqual(data["Test Item"][0]["cost"], 10.00)

    @patch("builtins.print")
    def test_read_csv_file_not_found(self, mock_print):
        """Test that a FileNotFoundError is handled."""
        read_csv("non_existent_file.csv")
        mock_print.assert_called_with("Error: The file was not found at 'non_existent_file.csv'")

    @patch("builtins.print")
    def test_read_csv_invalid_row(self, mock_print):
        """Test that a row with an incorrect number of columns is skipped."""
        invalid_csv_path = os.path.join(self.csv_dir, "invalid.csv")
        with open(invalid_csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["order_id", "order_date", "item_name", "is_food", "quantity", "price"])
            writer.writerow(["12345", "Jan 01, 2024", "Test Item", "unknown", "1"])
        
        read_csv(invalid_csv_path)
        mock_print.assert_called_with("Skipping row due to formatting error: ['12345', 'Jan 01, 2024', 'Test Item', 'unknown', '1']. Error: not enough values to unpack (expected 6, got 5)")

    def test_read_csv_empty_file(self):
        """Test that an empty file is handled correctly."""
        empty_csv_path = os.path.join(self.csv_dir, "empty.csv")
        with open(empty_csv_path, 'w', newline='', encoding='utf-8') as f:
            f.write("order_id,order_date,item_name,is_food,quantity,price\n")
        
        data = read_csv(empty_csv_path)
        self.assertEqual(data, {})

if __name__ == "__main__":
    unittest.main()
