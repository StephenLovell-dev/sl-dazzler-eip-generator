from datetime import datetime, timedelta
from dazzler.profiling import logEnd, logStart

class TestMain:

    def test_log_start(self):
      start = logStart('test_sid', 'someFunction')

    def test_log_end(self):
      start = datetime.now() - timedelta(days = 1)
      duration = logEnd('test_sid', 'someFunction', start)
      print(f'start {start} duration {duration}')