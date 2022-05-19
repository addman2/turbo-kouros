from turbokouros import *

def givemeconnector(setup):
    try:
        return LousyConnector(setup)
    except NotMyConnectorError:
        pass
    try:
        return LocalConnector(setup)
    except NotMyConnectorError:
        pass
    try:
        return SshConnector(setup)
    except NotMyConnectorError:
        pass
    raise UknownConnectorError()

