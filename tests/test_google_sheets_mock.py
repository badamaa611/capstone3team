import os
import unittest
from unittest.mock import patch, MagicMock

import google_sheets_api as gs


class TestGoogleSheetsMock(unittest.TestCase):
    def setUp(self):
        # Ensure a clean environment for each test
        os.environ.pop("MOCK_GOOGLE_SHEETS", None)

    def tearDown(self):
        os.environ.pop("MOCK_GOOGLE_SHEETS", None)

    def test_append_is_skipped_when_mock_env_true(self):
        os.environ['MOCK_GOOGLE_SHEETS'] = 'true'
        with patch('google_sheets_api.get_gspread_client') as mock_get:
            gs.append_test_result('Test Student', '12', 'Биологи', 10, 10)
            mock_get.assert_not_called()

    def test_append_calls_gspread_when_not_mocked(self):
        # Ensure mock flag is off
        os.environ.pop('MOCK_GOOGLE_SHEETS', None)

        # Create a fake gspread client -> sheet -> worksheet -> append_row
        mock_ws = MagicMock()
        mock_sh = MagicMock()
        mock_sh.worksheet.return_value = mock_ws
        mock_client = MagicMock()
        mock_client.open_by_key.return_value = mock_sh

        with patch('google_sheets_api.get_gspread_client', return_value=mock_client) as mock_get:
            gs.append_test_result('Alice', '11', 'Physics', 7, 10)
            mock_get.assert_called_once()
            mock_client.open_by_key.assert_called_once_with(gs.SHEET_ID)
            mock_sh.worksheet.assert_called_once_with("Үр дүн")
            mock_ws.append_row.assert_called()
            args, kwargs = mock_ws.append_row.call_args
            # Check that the first positional argument is the row list and contains the student name
            self.assertIsInstance(args[0], list)
            self.assertIn('Alice', args[0])
            # Ensure value_input_option kwarg is set to RAW
            self.assertEqual(kwargs.get('value_input_option'), 'RAW')


if __name__ == '__main__':
    unittest.main()
