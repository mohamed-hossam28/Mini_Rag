from helpers import get_settings, Settings


class BaseDataModel:
    def __init__(self,db_client:object):
        self.settings: Settings = get_settings()
        self.db_client = db_client