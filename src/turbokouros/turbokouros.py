#!/usr/bin/env python3 # PYTHON_ARGCOMPLETE_OK
import os
import sys
from turbokouros import *
import argparse
import argcomplete
import yaml
import logging

def check_directories(yamls = yamls):
    if not os.path.isdir(yamls):
        os.makedirs(yamls, exist_ok = True)

def get_options(optionfile = f"{root}/options.yaml"):
    check_directories()
    if not os.path.isfile(optionfile):
        with open(optionfile, "w") as fo:
            data = { "executable" : ["prep-mpi",
                                     "prep-serial",
                                     "turborvb-mpi",
                                     "turborvb-serial"],
                     "verbosity"  : 2 }
            yaml.dump(data, fo)
    with open(optionfile, "r") as fi:
        tree = yaml.full_load(fi)
    return tree

def read_yamls(yamls = yamls, name = None):
    ret = {}
    for d, dn, fn in os.walk(yamls):
        for f in fn:
            if f.endswith(".yaml"):
                path = f"{d}/{f}"
                with open(path, "r") as fi:
                    try:
                        tree = yaml.full_load(fi)
                    except:
                        continue
                if "name" not in tree: continue
                ret[tree["name"]] = { "tree": tree,
                                      "path": path }
        # Do not dive deeper
        break
    if name is not None:
        try:
            return ret[name]
        except:
            return None
    return ret

def complfun(prefix, parsed_args, **kwargs):
    return read_yamls().keys()

def main():
    options = get_options()
    logger = logging.getLogger('turbokouros')
    logger.setLevel(2)
    handler = logging.StreamHandler(sys.stdout)
    logger.addHandler(handler)

    parser = argparse.ArgumentParser(description='Turbo Kouros')
    parser.add_argument('-s',
                        '--show',
                        action="store_true")
    parser.add_argument('--protocol',
                        '-p',
                        nargs="+",
                        type=str,
                        default=None).completer = complfun
    parser.add_argument('--executable',
                        '-e',
                        nargs=1,
                        type=str,
                        choices = options["executable"],
                        default=options["executable"][0])
    parser.add_argument('--input',
                        '-i',
                        type=str,
                        default="turbo.input")

    argcomplete.autocomplete(parser)
    args = parser.parse_args()


    if args.show:
        msg = "Available protocols:\n"
        offset = 16
        fmt = logging.Formatter(f"%(proc)-{offset}s - %(message)-s")
        handler.setFormatter(fmt)
        for proc, val in read_yamls().items():
            desc = "No info"
            if "description" in val["tree"]:
                desc = val["tree"]["description"].strip().replace("\n", "\n" + " "*(3+offset))
            logger.log(2, desc, extra = {"proc" : proc})
        sys.exit(0)

    if args.protocol is not None:
        ret = read_yamls(name = args.protocol[0])
        if ret is None:
            logger.error("Uknown protocol")
            sys.exit(255)
        tree = ret["tree"]

        executable = args.executable
        if isinstance(executable, (list, tuple)):
            executable = executable[0]

        msg = f"Turbokouring executable {executable} with protocol {args.protocol[0]} containing {len(tree['communicator']['process'])} steps"
        logger.log(2, msg)
        settings = {"executable": executable,
                    "cmdlinp"   : args.input}
        c = Communicator(tree, settings)
        c.doit()

if __name__ == "__main__":
    main()
