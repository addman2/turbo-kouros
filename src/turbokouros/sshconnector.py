from turbokouros import *

import os
import yaml
import time
import random
import string
import subprocess
import paramiko

from pathlib import Path
from stat import S_ISDIR, S_ISREG

def parents_mkdir(sftp, directory):
    dir_path = str()
    for dir_folder in directory.split("/"):
        if dir_folder == "":
            continue
        dir_path += f"/{dir_folder}"
        try:
            sftp.listdir(dir_path)
        except IOError:
            sftp.mkdir(dir_path)

class SshConnector(Connector):

    """
    SSH connector for ssh execution
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.setup['type'].lower() not in ['ssh',
                                              'sshconnector']:
            raise NotMyConnectorError()

        try:
            self.address = self.setup["address"]
            rs = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(14))
            self.remote_wd = f'{self.setup["remote_wd"]}/{rs}'
            self.user = self.setup["user"]
        except KeyError as e:
            raise MissingNecessaryArtibuteError()

        self.port = 22
        self.key = None
        self.remove = True

        if "port" in self.setup:
            self.port = self.setup["port"]
        if "key" in self.setup:
            self.key = self.setup["key"]
        if "remove" in self.setup:
            self.remove = self.setup["remove"]

    def execute(self, cmd):
        cmd = f"cd {self.remote_wd}; {cmd}"
        stdin, stdout, stderr = self.ssh.exec_command(cmd)
        ret = "".join([ line for line in stdout ])
        return ret

    def get_files(self, filename, perm = False, allf = None, source = "./", destination = "./"):
        if allf == "dirs":
            for entry in self.sftp.listdir_attr(str(Path(self.remote_wd)/source)):
                if S_ISREG(entry.st_mode):
                    self.get_files(entry.filename, allf = None)
                if S_ISDIR(entry.st_mode):
                    try:
                        os.mkdir(str(entry.filename))
                    except FileExistsError:
                        pass
                    self.get_files(None, allf = "dirs", perm = perm, source = Path(source)/entry.filename, destination = Path(source)/entry.filename)
            return

        if allf == "files":
            for entry in self.sftp.listdir_attr(self.remote_wd):
                if S_ISREG(entry.st_mode):
                    self.get_files(entry.filename, allf = None)
            return

        try:
            self.sftp.get(f"{str(Path(source)/self.remote_wd)}/{filename}", str(Path(destination)/filename))
        except FileNotFoundError as exc:
            if not perm:
                raise exc

    def send_files(self, filename, perm = False, allf = None):
        if allf == "files":
            for f in os.listdir(os.getcwd()):
                self.send_files(f, allf = None)
            return
        dest = f"{self.remote_wd}/{filename}"

        try:
            self.sftp.put(filename, dest)
        except FileNotFoundError as exc:
            if not perm:
                raise exc

    def open_file(self, filename, stat):
        return self.sftp.file(filename, mode=stat)

    def remove_wd(self):
        with self as me:
            self.ssh.exec_command(f"rm {self.remote_wd}")

    def __enter__(self):
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy)
        settings = {"hostname" : self.address,
                    "port"     : self.port,
                    "username" : self.user}

        if self.key is None:
            settings["look_for_keys"] = True
        else:
            settings["key_filename"] = self.key

        for _ in range(3):
            try:
                client.connect(**settings)
                break
            except:
                time.sleep(1)
        self.ssh = client
        self.sftp = client.open_sftp()
        parents_mkdir(self.sftp, self.remote_wd)
        self.sftp.chdir(self.remote_wd)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.ssh.close()
        self.sftp.close()
