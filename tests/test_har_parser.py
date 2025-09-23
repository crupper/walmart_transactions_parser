
import unittest
import json
from unittest.mock import patch, mock_open
from har_parser import get_item_type

class TestGetItemType(unittest.TestCase):

    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open)
    def test_get_item_type_new_item(self, mock_file, mock_exists):
        """Test that a new item is added as 'unknown'."""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = json.dumps({})
        
        item_type = get_item_type("new_item")
        
        self.assertEqual(item_type, "unknown")
        mock_file.assert_called_with('food_or_non_food.json', 'w', encoding='utf-8')

    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open)
    def test_get_item_type_existing_item(self, mock_file, mock_exists):
        """Test that an existing item's type is returned."""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = json.dumps({"existing_item": "food"})
        
        item_type = get_item_type("existing_item")
        
        self.assertEqual(item_type, "food")

    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open)
    def test_get_item_type_file_not_found(self, mock_file, mock_exists):
        """Test that a new file is created if it doesn't exist."""
        mock_exists.return_value = False
        
        item_type = get_item_type("any_item")
        
        self.assertEqual(item_type, "unknown")
        mock_file.assert_called_with('food_or_non_food.json', 'w', encoding='utf-8')

if __name__ == "__main__":
    unittest.main()
