import os
import yaml
import subprocess
import paramiko

class NotMyConnectorError(BaseException):
    pass

class UknownConnectorError(BaseException):
    pass

class MissingNecessaryArtibuteError(BaseException):
    pass

class Protector:

    def __init__(self, f, obj):
        self._opened = False
        self.obj
        self.f = f

    def __call__(self, *args, **kwargs):
        self._opened = True
        return self.f(self.obj, *args, **kwargs)

    def say_yes(self, f):
        return f

class Connector:

    def __init__(self, setup, *args, **kwargs):
        self.setup = setup
        self._opened = False
        self.name = "Connector"
        if 'name' in setup:
            self.name = setup['name']

    def __enter__(self):
        return self

    def __exit__(self):
        pass

    def __call__(self, *args, **kwargs):
        return self.execute(*args, **kwargs)

    def get_file(self, filename):
        pass

    def send_file(self, filename):
        pass

    def open_file(self, filename, stat):
        pass

    def execute(self, *args, **kwargs):
        pass
