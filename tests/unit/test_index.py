from unittest.mock import MagicMock, patch
import os
from dazzler_nexts_generator.index import lambda_handler

class TestMain:

    def test_lambda_handler_pass(self):
        assert lambda_handler({}, None) is None

    def test_lambda_handler_throw(self):
        os.environ['DYNAMO_DB'] = 'test'
        assert lambda_handler({}, None) is None
        del os.environ['DYNAMO_DB']

    @patch('dazzler_nexts_generator.index.handleApiCall')
    def test_lambda_handler_ok(self, handleApiCall):
        handleApiCall.return_value='OK'
        os.environ['DYNAMO_DB'] = 'test'
        assert lambda_handler({'requestContext': None}, None) == 'OK'
        del os.environ['DYNAMO_DB']

