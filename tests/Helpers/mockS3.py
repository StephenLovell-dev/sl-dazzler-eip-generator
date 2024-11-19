
class StreamingBody:
    def __init__(self, a):
        self.a = a

    def read(self):
        return self.a

class MockS3:
    def __init__(self):
        self.state = {}

    def head_object(self, **kwargs):
        print('head_object', kwargs)
        return None
        
    def get_object(self, **kwargs):
        print('get_object', kwargs)
        return { 'Body': StreamingBody(self.state[kwargs['Key']]) }

    def put_object(self, **kwargs):
        print('put_object', kwargs)
        self.state[kwargs['Key']] = kwargs['Body'].encode(encoding='utf-8')
