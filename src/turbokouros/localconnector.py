from turbokouros import *

import os
import yaml
import shutil
import subprocess
import paramiko

class LocalConnector(Connector):

    """
    Basic local connector for local execution
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.setup['type'].lower() not in ['local',
                                              'lcl',
                                              'localconnector']:
            raise NotMyConnectorError()

        self.wd = None
        if "wd" in self.setup:
            self.wd = self.setup["wd"]
            os.makedirs(self.wd, exist_ok = True)

    def execute(self, cmd):
        if self.wd is not None:
            return subprocess.getoutput(f'cd {self.wd}; {cmd}')
        else:
            return subprocess.getoutput(f'cd {os.getcwd()}; {cmd}')

    def get_files(self, filename, allf = None):
        if self.wd is None:
            return

        if allf == "files":
            for f in next(os.walk(self.wd))[2]:
                self.get_files(f, allf = None)
            return

        try:
            shutil.copyfile(f'{self.wd}/{filename}',
                            filename,
                            follow_symlinks=True)
        except FileNotFoundError as exc:
            if not perm:
                raise exc

    def send_files(self, filename, allf = None):
        if self.wd is None:
            return

        if allf == "files":
            for f in next(os.walk(os.getcwd()))[2]:
                self.send_files(f, allf = None)
            return

        try:
            shutil.copyfile(filename,
                            f'{self.wd}/{filename}',
                            follow_symlinks=True)
        except FileNotFoundError as exc:
            if not perm:
                raise exc

    def open_file(self, filename, stat):
        return open(filename, stat)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
