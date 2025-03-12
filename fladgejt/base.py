class BaseClient:
    def __init__(self, context):
        self.context = context

    def check_connection(self):
        pass

    def prepare_for_rpc(self):
        self.last_rpc_failed = False

    def logout(self):
        pass

    fake_time_msec = None

    last_rpc_failed = False
