
import unittest
from unittest.mock import MagicMock
import sys
import threading
import time

# Mock flet before importing main
sys.modules["flet"] = MagicMock()
import flet as ft

# Now import main
import main

class TestMain(unittest.TestCase):
    def test_main_initialization(self):
        print("Testing main initialization...")
        # Create a mock page
        page = MagicMock()
        page.data = {}
        
        # Capture what is added to page
        added_controls = []
        def mock_add(*controls):
            added_controls.extend(controls)
        page.add.side_effect = mock_add
        
        # Run main
        try:
            main.main(page)
            print("Main executed successfully")
        except Exception as e:
            self.fail(f"Main raised an exception: {e}")
            
        # Verify controls were added
        self.assertTrue(len(added_controls) > 0, "No controls were added to the page")
        print(f"Added {len(added_controls)} high-level controls")
        
        # Check basic properties
        self.assertEqual(page.title, "Calculadora Crypto & BCV")
        
        # Check if background thread started
        # This is harder to test without mocking threading, but we can check if logic allows it
        # We mainly care if main() finishes without error.

if __name__ == "__main__":
    unittest.main()
