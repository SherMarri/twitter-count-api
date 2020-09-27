import unittest
import json
import os

from src import settings
from src import handler


def get_body():
  return {
    'body': json.dumps({
      'fromDate': '2020-03-12',
      'toDate': '2020-03-22',
      'query': 'profile_country:ES (COVID19)'
    })
  }

class TestTweetCountLambda(unittest.TestCase):
  """
  Unit tests for lambda function
  """
  def test_valid_result_format(self):
    '''
    statusCode: 200 => Test that lambda returns data in correct format
    '''
    result = handler.counts(get_body(), None)
    self.assertIn('statusCode', result)
    self.assertIn('headers', result)
    self.assertIn('body', result)
    self.assertEqual(result['statusCode'], 200)
    self.assertIsInstance(result['body'], str)
    body = json.loads(result['body'])
    self.assertIsInstance(body, dict)
    self.assertIn('count', body)
    self.assertIsInstance(body['count'], int)

  def test_invalid_result_format(self):
    '''
    statusCode: 422 => Test that lambda returns error response in correct format
    '''
    req_body = {
      'body': json.dumps({
        'fromDate': '2020-03-12',
        'query': 'profile_country:ES (COVID19)'
      })  # Without toDate, will return error
    }
    result = handler.counts(req_body, None)
    self.assertIn('statusCode', result)
    self.assertIn('headers', result)
    self.assertIn('body', result)
    self.assertEqual(result['statusCode'], 422)
    self.assertIsInstance(result['body'], str)
    body = json.loads(result['body'])
    self.assertIsInstance(body, dict)
    self.assertIn('message', body)
    self.assertIsInstance(body['message'], str)

  def test_missing_inputs(self):
    '''
    Test that the lambda properly verifies the presence of all inputs
    '''
    # Missing toDate
    req_body = {
      'body': json.dumps({
        'fromDate': '2020-03-12',
        'query': 'profile_country:ES (COVID19)'
      })
    }
    result = handler.counts(req_body, None)
    self.assertEqual(result['statusCode'], 422)
    message = json.loads(result['body'])['message']
    self.assertEqual(message, 'toDate is missing')

    # Missing fromDate
    req_body = {
      'body': json.dumps({
        'toDate': '2020-03-12',
        'query': 'profile_country:ES (COVID19)'
      })
    }
    result = handler.counts(req_body, None)
    self.assertEqual(result['statusCode'], 422)
    message = json.loads(result['body'])['message']
    self.assertEqual(message, 'fromDate is missing')

    # Missing query
    req_body = {
      'body': json.dumps({
        'toDate': '2020-03-22',
        'fromDate': '2020-03-12',
      })
    }
    result = handler.counts(req_body, None)
    self.assertEqual(result['statusCode'], 422)
    message = json.loads(result['body'])['message']
    self.assertEqual(message, 'query is missing')

  def test_date_range(self):
    req_body = {
      'body': json.dumps({
        'fromDate': '2020-04-12',
        'toDate': '2020-03-12',
        'query': 'profile_country:ES (COVID19)'
      })
    }
    result = handler.counts(req_body, None)
    self.assertEqual(result['statusCode'], 422)
    message = json.loads(result['body'])['message']
    self.assertEqual(message, 'from date cannot be after to date')

  def test_date_gap(self):
    req_body = {
      'body': json.dumps({
        'fromDate': '2020-04-12',
        'toDate': '2020-05-22',
        'query': 'profile_country:ES (COVID19)'
      })
    }
    result = handler.counts(req_body, None)
    self.assertEqual(result['statusCode'], 422)
    message = json.loads(result['body'])['message']
    self.assertEqual(message, 'date range cannot be greater than 31 days')

  def test_date_format(self):
    req_body = {
      'body': json.dumps({
        'fromDate': 'AAA-04-12',
        'toDate': '2020-02-12',
        'query': 'profile_country:ES (COVID19)'
      })
    }
    result = handler.counts(req_body, None)
    self.assertEqual(result['statusCode'], 422)
    message = json.loads(result['body'])['message']
    self.assertEqual(message, 'date format must be YYYY-MM-DD')

  def test_http_code(self):
    original = os.environ['ACCOUNT_USERNAME']
    os.environ['ACCOUNT_USERNAME'] = 'fake'
    result = handler.counts(get_body(), None)
    os.environ['ACCOUNT_USERNAME'] = original
    self.assertEqual(result['statusCode'], 400)
    message = json.loads(result['body'])['message']
    self.assertEqual(message, 'Twitter API failed to process your request.')