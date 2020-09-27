import datetime
import os
import traceback
from searchtweets import collect_results, gen_rule_payload, load_credentials
from searchtweets.credentials import _parse_credentials
from collections import deque

from src.api.exceptions import ValidationError


class TweetCounter:
  def __init__(self, credentials):
    self.credentials = self._validate_credentials(credentials)

  def count(self, dataset, date_range=None):
    self._validate_dataset(dataset)
    date_range = self._validate_date_range(date_range)
    tweets_count = self._get_count_tweets(dataset, date_range)
    return sum([t['count'] for t in tweets_count])

  def _get_count_tweets(self, dataset, date_range):
    credentials = self._get_credentials()
    payload = gen_rule_payload(
      '-is:retweet {}'.format(dataset['query']), # exclude retweets
      results_per_call=500,
      count_bucket="day",
      from_date=date_range['from'],
      to_date=date_range['to'],
    )
    return collect_results(payload, result_stream_args=credentials)

  
  def _get_credentials(self):
    credential_vars = {
      'endpoint': self.credentials['endpoint'],
      'username': self.credentials['username'],
      'password': self.credentials['password']
    }
    parsed_vars = _parse_credentials(credential_vars, account_type=self.credentials['account_type'])
    return parsed_vars

  def _validate_credentials(self, credentials):
    if type(credentials) is not dict:
      raise TypeError("credentials argument must be a dictionary.")

    keys = ['endpoint', 'username', 'password', 'account_type']
    for key in keys:
      if key in credentials.keys():
        if type(credentials[key]) is not str:
          raise TypeError(f"{key} in credentials must be a string.")
      else:
        raise KeyError(f"{key} is missing in credentials")
    return credentials

  def _sanitize_query(self, query):
    """
    Util for sanitizing the query string
    1. Remove spaces from the beginning and the end (trim)
    2. Clean double spaces (or more than two consecutive space)
    3. Replace "+" with spaces
    """
    return ' '.join(query.replace(' + ', ' ').strip().split())

  def _validate_dataset(self, dataset):
    if type(dataset) is not dict:
      raise TypeError("dataset argument must be a dictionary")
    if 'query' not in dataset.keys():
      raise ValidationError("query key not found in dataset")
    if not isinstance(dataset['query'], str):
      raise ValidationError("query must be a string")
    query = self._sanitize_query(dataset['query'])
    if len(query) == 0:
      raise ValidationError("query cannot be empty")
    query_length = len(query) + len(os.getenv('QUERY_PREFIX'))
    if query_length > int(os.getenv('QUERY_LENGTH')):
      raise ValidationError(f"query cannot be longer than {os.getenv('QUERY_LENGTH')} characters")
    self._validate_query_syntax(query)
    return {
      'query': query
    }

  def _validate_date_range(self, date_range):
    format = "%Y-%m-%d"
    if date_range is not None:
      if type(date_range) is not dict:
        raise TypeError("date_range must be a dictionary")
      if 'from' not in date_range.keys():
        raise ValidationError("from key not found in date_range")
      if 'to' not in date_range.keys():
        raise ValidationError("to key not found in date_range")
      try:
        from_date = datetime.datetime.strptime(date_range['from'], format)
        to_date = datetime.datetime.strptime(date_range['to'], format)
      except:
        raise ValidationError('date format must be YYYY-MM-DD')
      if from_date > to_date:
        raise ValidationError('from date cannot be after to date')
      delta = to_date - from_date
      if delta.days > 31:
        raise ValidationError('date range cannot be greater than 31 days')
      return date_range
    else:
      to_date = datetime.datetime.today()
      from_date = to_date - datetime.timedelta(days=31)
      return {
        'from': from_date.strftime(format),
        'to': to_date.strftime(format),
      }

  def _validate_parenthesis(self, query):
    parenthesis = deque()
    for c in query:
      if c in '{([])}':
        parenthesis.append(c)
    
    p_map = {
      '{': '}',
      '(': ')',
      '[': ']'
    }
    opening_parenthesis = []
    for p in parenthesis:
      try:
        if p in '{[(':
          opening_parenthesis.append(p)
        else:
          left = opening_parenthesis.pop()
          if p_map[left] != p:
            raise ValidationError('mismatching parenthesis in query')
      except IndexError:
        raise ValidationError('mismatching parenthesis in query')
    if len(opening_parenthesis) > 0:
      raise ValidationError('mismatching parenthesis in query')
    return True

  def _validate_double_ors(self, query):
    if 'OROR' in query or 'OR OR' in query:
      raise ValidationError('invalid expression in query')
    return True

  def _validate_query_syntax(self, query):
    self._validate_parenthesis(query)
    self._validate_double_ors(query)
    return True
