from turbokouros import *
import re
import copy
import time
import logging

class Communicator:

    def __init__(self, setup, settings):
        self.setup = setup
        self._notparsed = setup["communicator"]
        self.settings = settings
        self.logger = logging.getLogger("turbokouros")
        if self.settings is not None:
            if "var" not in self._notparsed:
                self._notparsed["var"] = {}
            for key, val in self._notparsed["var"].items():
                for key_, val_ in self.settings.items():
                    r = val.replace(f"%%{key_}%%", val_)
                    self._notparsed[key] = r
            self._notparsed["var"].update(self.settings)
        self.conn = givemeconnector(setup["connector"])

    @property
    def parsed(self):
        ret = copy.deepcopy(self._notparsed)
        # Do the variables first
        if "var" in self._notparsed:
            variables = self._notparsed["var"]
            self._iterate_dict(ret, variables)
        return ret

    # Try to figure out how to move these two funcs into separed file
    def _iterate_dict(self, d, variables):
        for k in d:
            if isinstance(d[k], dict):
                self._iterate_dict(d[k], variables)
            elif isinstance(d[k], list):
                self._iterate_list(d[k], variables)
            elif isinstance(d[k], tuple):
                d[k] = list(d[k])
                self._iterate_list(d[k], variables)
            elif isinstance(d[k], str):
                for vark, varv in variables.items():
                    d[k] = d[k].replace(f"%%{vark}%%", varv)
            elif isinstance(d[k], (int, float)):
                d[k] = f"{d[k]}"
                for vark, varv in variables.items():
                    d[k] = d[k].replace(f"%%{vark}%%", varv)
            elif d[k] is None:
                pass
            else:
                self.logger.error(f"I dont know what this is {type(d)}\n{d[k]}")
                raise

    def _iterate_list(self, d, variables):
        for ii in range(len(d)):
            if isinstance(d[ii], dict):
                self._iterate_dict(d[ii], variables)
            elif isinstance(d[ii], list):
                self._iterate_list(d[ii], variables)
            elif isinstance(d[ii], tuple):
                d[k] = list(d[ii])
                self._iterate_list(d[ii], variables)
            elif isinstance(d[ii], str):
                for vark, varv in variables.items():
                    d[ii] = d[ii].replace(f"%%{vark}%%", varv)
            elif d[ii] is None:
                pass
            else:
                raise

    def doit(self):
        total = len(self.parsed["process"])
        for ii, item in enumerate(self.parsed["process"]):
            op, s = list(item.items())[0]
            msg = f"Operation {ii+1}/{total}: {op}"
            self.logger.log(2, msg)
            if op == "copy":
                self.copy_files(s)
            if op == "execute":
                self.execute(s)
            if op == "sleep":
                self.sleep(s)
            if op == "makefile":
                self.makefile(s)
            if op == "submit":
                self.submit(s)
            if op == "remove_wd":
                self.remove_wd(s)

    def copy_files(self, setup):
        perm = False
        try:
            perm = setup["ifexists"]
        except:
            pass

        if "all" in setup:
            if setup["all"] in ["files", "dirs"]:
                if setup["direction"] == "to":
                    with self.conn as con:
                        con.send_files(None,
                                       allf = setup["all"])
                if setup["direction"] == "from":
                    with self.conn as con:
                        con.get_files(None,
                                      allf = setup["all"])
                return

        for f in setup["files"]:
            if setup["direction"] == "to":
                with self.conn as con:
                    con.send_files(f, perm = perm)
            if setup["direction"] == "from":
                with self.conn as con:
                    con.get_files(f, perm = perm)

    def execute(self, cmd):
        cmd = f"{self.set_environment()} {cmd}"
        with self.conn as con:
            con(cmd)

    def submit(self, setup):
        cmd = f"{self.set_environment()} {setup['submit_command']}"
        period = 5.0
        if "period" in setup:
            period = float(setup["period"])
        prog = re.compile("Submitted batch job ([0-9]+)",
                          re.MULTILINE)
        with self.conn as con:
            jobid = prog.search(con(cmd)).group(1)

        while True:
            time.sleep(period)
            with self.conn as con:
                stat = con(setup["stat_command"])
            with open("last.stat", "w") as fo:
                fo.write(stat)
            if jobid not in stat:
                break

    def makefile(self, setup):
        with self.conn as con:
            f = con.open_file(setup["filename"],
                              "w")
            for line in setup["lines"]:
                f.write(f"{line}\n")

    def set_environment(self):
        ret = ""
        if "environment" not in self.parsed:
            return ret
        ret = ";".join([ cmd for cmd in self.parsed["environment"] ]) + ";"
        return ret

    def sleep(self, sleep_time):
        time.sleep(float(sleep_time))

    def remove_wd(self, setup):
        self.conn.remove_wd()
