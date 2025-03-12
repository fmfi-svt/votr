class BaseClient:
    def __init__(self, context):
        self.context = context

    def check_connection(self):
        pass

    def logout(self):
        pass

    fake_time_msec = None
