class ValidationError(Exception):
  """
  Exception raised for invalid inputs
  """
  def __init__(self, message=None):
    self.message = message
    super().__init__(message)