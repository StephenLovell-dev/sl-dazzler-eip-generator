# This class is used to build a response object returned by requests module
class MockRequestResponse(object):
    def raise_for_status(self):
        print('called raise_for_status')
    def json(self):
        print('self.content', self.content)
        return self.content

    def __init__(self, my_dict):
        for key in my_dict:
            setattr(self, key, my_dict[key])

class MockRequestErrorResponse():
    def raise_for_status(self):
        print('called raise_for_status')
    def json(self):
        print('Error', self.errorMsg)
        raise Exception(self.errorMsg)

    def __init__(self, error_message):
        self.errorMsg = error_message
