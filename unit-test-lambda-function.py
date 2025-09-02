import unittest
from unittest.mock import patch, MagicMock
import json
import lambda_function  # your lambda function file name

class TestLambdaHandler(unittest.TestCase):

    @patch('lambda_function.dynamodb')
    def test_lambda_handler_existing_item(self, mock_dynamodb):
        # Mock table and get_item response
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_table.get_item.return_value = {'Item': {'id': '1', 'views': 5}}

        event = {}
        context = {}

        response = lambda_function.lambda_handler(event, context)

        # Assertions
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertEqual(body['views'], 6)  # incremented

        # Check that put_item was called with updated views
        mock_table.put_item.assert_called_with({'id': '1', 'views': 6})

    @patch('lambda_function.dynamodb')
    def test_lambda_handler_new_item(self, mock_dynamodb):
        # Mock table and get_item with no Item
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_table.get_item.return_value = {}

        event = {}
        context = {}

        response = lambda_function.lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertEqual(body['views'], 1)  # new item starts at 1

        mock_table.put_item.assert_called_with({'id': '1', 'views': 1})

    @patch('lambda_function.dynamodb')
    def test_lambda_handler_exception(self, mock_dynamodb):
        # Force get_item to throw an exception
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_table.get_item.side_effect = Exception("DynamoDB error")

        event = {}
        context = {}

        response = lambda_function.lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 500)
        body = json.loads(response['body'])
        self.assertIn('error', body)
        self.assertEqual(body['error'], 'DynamoDB error')

if __name__ == '__main__':
    unittest.main()
