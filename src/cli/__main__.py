import os
import sys
from requests.exceptions import HTTPError
import traceback

from src import settings
from src.api.exceptions import ValidationError
from src.api import tweet_counter


CREDENTIALS = {
  'endpoint': os.getenv('API_ENDPOINT'),
  'username': os.getenv('ACCOUNT_USERNAME'),
  'password': os.getenv('ACCOUNT_PASSWORD'),
  'account_type': os.getenv('ACCOUNT_TYPE')
}

def parse_arguments():
  arguments = {}
  if len(sys.argv) == 2:  # If date range not provided
    return {
      'query': sys.argv[1],
    }
  if len(sys.argv) != 4:
    print("Invalid number of arguments supplied.")
    print(f"Usage: python {sys.argv[0]} '<query>'")
    print(f"Example: python {sys.argv[0]} 'profile_country:ES (COVID19)'")
    print("Or")
    print(f"Usage: python {sys.argv[0]} '<query>' <from> <to>")
    raise SystemExit(f"Usage: python {sys.argv[0]} 'profile_country:ES (COVID19)' 2020-04-30 2020-05-31")
  return {
    'query': sys.argv[1],
    'date_range': {
      'from': sys.argv[2],
      'to': sys.argv[3]
    }
  }


if __name__ == "__main__":
  arguments = parse_arguments()
  
  dataset = {
    'query':arguments['query']
  }
  date_range = arguments['date_range'] if 'date_range' in arguments.keys() else None
  
  tc = tweet_counter.TweetCounter(CREDENTIALS)
  try:
    count = tc.count(dataset, date_range)
    print(count)
  except ValidationError as err:
    print(err.message)
    traceback.print_tb(err.__traceback__)
  except HTTPError:
    print('Twitter API failed to process your request.')
  except Exception as err:
    print(str(err))
    traceback.print_tb(err.__traceback__)

