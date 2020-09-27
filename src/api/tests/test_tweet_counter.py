import unittest
import os
import datetime

from src.api.tweet_counter import TweetCounter
from src import settings
from src.api.exceptions import ValidationError

# profile_country:ES (COVID19)
dataset = {
  'query': 'profile_country:ES (COVID19)'
}

def get_credentials():
  return {
    'endpoint': os.getenv('API_ENDPOINT'),
    'username': os.getenv('ACCOUNT_USERNAME'),
    'password': os.getenv('ACCOUNT_PASSWORD'),
    'account_type': os.getenv('ACCOUNT_TYPE')
  }


class TestTweetCounter(unittest.TestCase):

  def test_invalid_dataset(self):
    '''
    Verifies the format of dataset dictionary
    '''
    counter = TweetCounter(get_credentials())
    with self.assertRaises(TypeError):
      counter.count(1)  # Pass integer instead of a dictionary
    
    with self.assertRaises(ValidationError):
      counter.count({})  # Pass a dictionary but without 'query' key
    
    with self.assertRaises(ValidationError) as err:
      counter.count({'query': 1}) # Pass an integer as query value
      self.assertEqual(err.message, 'query must be a string')

    # Test query length considering -is-retweet prefix
    original = os.environ['QUERY_LENGTH']
    os.environ['QUERY_LENGTH'] = str(15)
    with self.assertRaises(ValidationError) as err:
      count = counter.count({'query': 'hello'})
      self.assertEqual(err.message, f"query cannot be longer than {os.getenv('QUERY_LENGTH')} characters")
    os.environ['QUERY_LENGTH'] = original

  def test_query_sanitization(self):
    '''
    Verifies that the query is being sanitized correctly
    '''
    counter = TweetCounter(get_credentials())
    self.assertTrue(hasattr(counter, '_sanitize_query'))
    
    # Trims the query
    query = '  hello  ' 
    self.assertEqual(counter._sanitize_query(query), 'hello')
    
    # Removes double/consecutive spaces
    query = 'hello   there'
    self.assertEqual(counter._sanitize_query(query), 'hello there')

    # Replaces + with spaces
    query = 'hello + there'
    self.assertEqual(counter._sanitize_query(query), 'hello there')

  def test_query_syntax_validation(self):
    '''
    Verifies that the query syntax is correct
    '''
    counter = TweetCounter(get_credentials())
    self.assertTrue(hasattr(counter, '_validate_query_syntax'))
    self.assertTrue(hasattr(counter, '_validate_parenthesis'))
    
    # Validates matching parenthesis
    query = 'hello (good OR bad)'
    self.assertTrue(counter._validate_parenthesis(query))

    # Validates mismatching parenthesis
    query = 'hello (}}}'
    with self.assertRaises(ValidationError):
      counter._validate_parenthesis(query)
    
    query = '('
    with self.assertRaises(ValidationError) as err:
      counter._validate_parenthesis(query)
      self.assertEqual(err.message, 'mismatching parenthesis in query')
    
    query = '()]'
    with self.assertRaises(ValidationError) as err:
      counter._validate_parenthesis(query)
      self.assertEqual(err.message, 'mismatching parenthesis in query')

    # Validate double ors
    query = 'OR'
    self.assertTrue(counter._validate_double_ors(query))

    query = 'OROR'
    with self.assertRaises(ValidationError) as err:
      counter._validate_double_ors(query)
      self.assertEqual(err.message, 'invalid expression in query')

    query = 'OR OR'
    with self.assertRaises(ValidationError) as err:
      counter._validate_double_ors(query)
      self.assertEqual(err.message, 'invalid expression in query')

    query = 'ORoR'
    self.assertTrue(counter._validate_double_ors(query))

    query = ('thread.country:ES (site_type:discussions OR site_type:blogs OR ' +
      ' site_type:news) AND (Barcelona OR BCN)')
    self.assertTrue(counter._validate_query_syntax(query))

    query = ('thread.country:ES (site_type:discussions OR site_type:blogs OR ' +
      'site_type:news) AND (Barcelona OR BCN))')
    with self.assertRaises(ValidationError) as err:
      counter._validate_query_syntax(query)
      self.assertEqual(err.message, 'mismatching parenthesis in query')

    query = ('thread.country:ES (site_type:discussions OR site_type:blogs OR ' +
      'site_type:news) AND (Barcelona OR BCN))')
    with self.assertRaises(ValidationError) as err:
      counter._validate_query_syntax(query)
      self.assertEqual(err.message, 'mismatching parenthesis in query')

    query = ('tthread.country:ES (site_type:discussions OR site_type:blogs OR ' +
      'site_type:news)) AND (Barcelona OR BCN)')
    with self.assertRaises(ValidationError) as err:
      counter._validate_query_syntax(query)
      self.assertEqual(err.message, 'mismatching parenthesis in query')
    
    # Does not replace + with space in 'hello+there'
    query = 'hello+there'
    self.assertEqual(counter._sanitize_query(query), query)

    # Does not replace + with space in '+disney'
    query = '+disney'
    self.assertEqual(counter._sanitize_query(query), query)

    # Does not replace + with space in 'disney+'
    query = 'disney+'
    self.assertEqual(counter._sanitize_query(query), query)



  def test_invalid_date_range(self):
    '''
    Verifies the date range parameter
    '''
    counter = TweetCounter(get_credentials())
    # Test date_range type
    with self.assertRaises(TypeError):
      counter.count(dataset, date_range=False)

    # Test date_range missing keys 'from'
    with self.assertRaises(ValidationError):
      counter.count(dataset, date_range={'to': '2020-05-03'})

    # Test date_range missing keys 'to'
    with self.assertRaises(ValidationError):
      counter.count(dataset, date_range={'from': '2020-05-03'})

    # Test date format 'from'
    with self.assertRaises(ValidationError) as ex:
      counter.count(dataset, date_range={'from': '2020-30-45', 'to': '2020-05-06'})
    
    # Test date format 'to'
    with self.assertRaises(ValidationError) as ex:
      counter.count(dataset, date_range={'from': '2020-05-06', 'to': '2020-30-45'})

    # Test from > to
    with self.assertRaises(ValidationError) as ex:
      counter.count(dataset, date_range={'from': '2020-05-03', 'to': '2020-04-03'})
      self.assertEqual(ex.message, 'from date cannot be after to date')

    # Test: gap should not be greater than 31 days
    with self.assertRaises(ValidationError) as ex:
      counter.count(dataset, date_range={'from': '2020-03-03', 'to': '2020-05-03'})
      self.assertEqual(ex.message, 'date range cannot be greater than 31 days')

  def test_return_value(self):
    '''
    Verifies that the return value is an integer.
    '''
    counter = TweetCounter(get_credentials())
    count = counter.count(dataset, date_range={'from': '2020-04-21', 'to': '2020-05-11'})
    self.assertTrue(type(count) is int)

  def test_invalid_credentials(self):
    '''
    Verifies the credentials
    '''
    # Test credentials type
    with self.assertRaises(TypeError) as ex:
      counter = TweetCounter(1)
      self.assertEqual(ex.message, 'credentials argument must be a dictionary.')

    # Test missing keys in credentials
    # 1. endpoint
    with self.assertRaises(KeyError) as ex:
      credentials = get_credentials()
      del credentials['endpoint']
      counter = TweetCounter(credentials)
      self.assertEqual(ex.message, 'endpoint is missing in credentials')

    # 2. username
    with self.assertRaises(KeyError) as ex:
      credentials = get_credentials()
      del credentials['username']
      counter = TweetCounter(credentials)
      self.assertEqual(ex.message, 'username is missing in credentials')

    # 3. password
    with self.assertRaises(KeyError) as ex:
      credentials = get_credentials()
      del credentials['password']
      counter = TweetCounter(credentials)
      self.assertEqual(ex.message, 'password is missing in credentials')

    # 4. account_type
    with self.assertRaises(KeyError) as ex:
      credentials = get_credentials()
      del credentials['account_type']
      counter = TweetCounter(credentials)
      self.assertEqual(ex.message, 'account_type is missing in credentials')
