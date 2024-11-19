from botocore.exceptions import ClientError
from medialivehelpers.schedule_items import ScheduleItems

class Schedule:
    def __init__(self, sid, channelId, client):
        self.sid = sid
        self.channelId = channelId
        self.client = client

    """
    An error occurred (UnprocessableEntityException) when calling the BatchUpdateSchedule operation: 
    actionName: 2021-07-12T22'13'00Z PT8M24S sched p094hcczv1 
    error: Cannot schedule actionName=2021-07-12T22'13'00Z PT8M24S sched p094hcczv1 
    with action time=2021-07-12T22:13:00Z, missed deadline of 15 seconds
    """
    """
    An error occurred (UnprocessableEntityException) when calling the BatchUpdateSchedule operation:
    schedule_actions[1].schedule_action_start_settings.time actionName: 2021-09-14T09'23'55Z PT30S slate 
    error: Input switch actions must be separated by at least 5 seconds; violation found 
    between action names [2021-09-14T09'23'54Z PT30S slate] and [2021-09-14T09'23'55Z PT30S slate].
    """
    """
    An error occurred (UnprocessableEntityException) when calling the BatchUpdateSchedule operation:
    schedule_actions[1].schedule_action_start_settings.reference_action_name actionName: 2021-09-14T13'47'20Z PT1M48S loop A_Con...er error: Reference action name 2021-09-14T13'46'50Z PT30S slate is used for multiple input switch follow actions. 
    Only one input switch can follow another.; 
    schedule_actions[2].schedule_action_start_settings.reference_action_name actionName: 2021-09-14T13'47'20Z PT1M8S loop Agath...er error: Reference action name 2021-09-14T13'46'50Z PT30S slate is used for multiple input switch follow actions. 
    Only one input switch can follow another.
    """
    """
    An error occurred (ConflictException) when calling the BatchUpdateSchedule operation: 
    Resource has been changed by another request, please re-submit
    """
    def add(self, actions):
        print(self.sid, 'schedule add', actions)
        try:
            r = self.client.batch_update_schedule(
                ChannelId=self.channelId,
                Creates={ 'ScheduleActions': actions }
            )
            print(self.sid, "added schedule items in", self.channelId)
            return True
        except ClientError as error:
            print(self.sid, "error adding schedule items in", self.channelId)
            print(self.sid, error.response)
            if error.response['Error']['Code'] == "UnprocessableEntityException":
                print(self.sid, error.response['Error']['Message'])
                print(self.sid, 'request was to add', actions)
                print(self.sid, 'existing schedule was', self._describe())
            else:
                raise error
        return False

    def delete_items(self, actionNames):
        print(self.sid, "Deleting Schedule Items")
        try:
            r = self.client.batch_update_schedule(
                ChannelId=self.channelId,
                Deletes={
                    'ActionNames': actionNames
                }
            )
            print("deleted %d items from %s" % (len(actionNames), self.channelId ))
        except ClientError as e:
            print("error deleting schedule items in", self.channelId)
            print(e)

    def replace(self, newActions, oldActionNames):
        print(self.sid, 'schedule replace', newActions, oldActionNames)
        try:
            r = self.client.batch_update_schedule(
                ChannelId=self.channelId,
                Creates={ 'ScheduleActions': newActions },
                Deletes={
                    'ActionNames': oldActionNames
                }
            )
            print(self.sid, "added schedule items in", self.channelId)
            return True
        except ClientError as error:
            print(self.sid, "error adding schedule items in", self.channelId)
            print(self.sid, error.response)
            if error.response['Error']['Code'] == "UnprocessableEntityException":
                print(self.sid, error.response['Error']['Message'])
                print(self.sid, 'request was to add', newActions, 'and remove', oldActionNames)
                print(self.sid, 'existing schedule was', self._describe())
            else:
                raise error
        return False

    def _describe(self):
        #Result is paginated
        schedule_action = []
        token = None
        print (f"MedialiveSchedule _describe sid {self.sid} channel_is {self.channelId}")
        while True:
            if token is not None:
                response = self.client.describe_schedule(
                    ChannelId=self.channelId,
                    NextToken=token
                )
            else:
                response = self.client.describe_schedule(
                    ChannelId=self.channelId,
                )
            schedule_action.extend(response['ScheduleActions'])
            if 'NextToken' in str(response):
                token = response['NextToken']
            else:
                1==1 # just here for code coverage
                break
        return schedule_action

    def describe(self):
        try:
            return ScheduleItems(self._describe())
        except ClientError as e:
            print(e)
