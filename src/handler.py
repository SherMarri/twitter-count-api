import os
import json
import traceback
from requests.exceptions import HTTPError

from src.api import tweet_counter
from src.api.exceptions import ValidationError

def get_credentials():
  return {
    'endpoint': os.getenv('API_ENDPOINT'),
    'username': os.getenv('ACCOUNT_USERNAME'),
    'password': os.getenv('ACCOUNT_PASSWORD'),
    'account_type': os.getenv('ACCOUNT_TYPE')
  }

def response(code, data):
  return {
    'statusCode': code,
    'headers': {
        'content-type': 'application/json; charset=utf-8'
    },
    'body': json.dumps(data)
  }


def validate_inputs(inputs):
  dataset = None
  date_range = None
  if 'query' not in inputs:
      raise ValidationError('query is missing')
  dataset = {
    'query': inputs['query']
  }
  if 'fromDate' in inputs or 'toDate' in inputs:
    keys = ['fromDate', 'toDate']
    for key in keys:
      if key not in inputs:
        raise ValidationError(f'{key} is missing')
    date_range = {
      'from': inputs['fromDate'],
      'to': inputs['toDate']
    }
  return dataset, date_range


def counts(event, context):
  try:
    body = json.loads(event['body'])
    dataset, date_range = validate_inputs(body)
    tc = tweet_counter.TweetCounter(get_credentials())
    count = tc.count(dataset, date_range)
    return response(200, {'count': count})
  except ValidationError as err:
    return response(422, {'message': err.message})
  except HTTPError:
    return response(400, {'message': 'Twitter API failed to process your request.'})
  except Exception as err:
    print(err)
    traceback.print_tb(err.__traceback__)
    return response(500, {'message': 'Something unexpected occurred. Please check your request or try again later.'})
