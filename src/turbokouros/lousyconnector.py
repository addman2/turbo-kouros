from turbokouros import *

class LousyConnector(Connector):

    """
    Connector made for testing, don't use this one
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.setup['type'].lower() not in ['lousy']:
            raise NotMyConnectorError()
