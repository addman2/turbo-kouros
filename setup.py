import os
from setuptools.command.develop import develop
from setuptools.command.install import install
from setuptools import setup
from setuptools import find_packages

f = '''
# Run something, muting output or redirecting it to the debug stream
# depending on the value of _ARC_DEBUG.
# If ARGCOMPLETE_USE_TEMPFILES is set, use tempfiles for IPC.
__python_argcomplete_run() {
    if [[ -z "${ARGCOMPLETE_USE_TEMPFILES-}" ]]; then
        __python_argcomplete_run_inner "$@"
        return
    fi
    local tmpfile="$(mktemp)"
    _ARGCOMPLETE_STDOUT_FILENAME="$tmpfile" __python_argcomplete_run_inner "$@"
    local code=$?
    cat "$tmpfile"
    rm "$tmpfile"
    return $code
}

__python_argcomplete_run_inner() {
    if [[ -z "${_ARC_DEBUG-}" ]]; then
        "$@" 8>&1 9>&2 1>/dev/null 2>&1
    else
        "$@" 8>&1 9>&2 1>&9 2>&1
    fi
}

_python_argcomplete() {
    local IFS=$'\013'
    local SUPPRESS_SPACE=0
    if compopt +o nospace 2> /dev/null; then
        SUPPRESS_SPACE=1
    fi
    COMPREPLY=( $(IFS="$IFS" \\
                  COMP_LINE="$COMP_LINE" \\
                  COMP_POINT="$COMP_POINT" \\
                  COMP_TYPE="$COMP_TYPE" \\
                  _ARGCOMPLETE_COMP_WORDBREAKS="$COMP_WORDBREAKS" \\
                  _ARGCOMPLETE=1 \\
                  _ARGCOMPLETE_SUPPRESS_SPACE=$SUPPRESS_SPACE \\
                  __python_argcomplete_run "$1") )
    if [[ $? != 0 ]]; then
        unset COMPREPLY
    elif [[ $SUPPRESS_SPACE == 1 ]] && [[ "${COMPREPLY-}" =~ [=/:]$ ]]; then
        compopt -o nospace
    fi
}
complete -o nospace -o default -o bashdefault -F _python_argcomplete turbo-kouros
'''

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

def add2act(f = f):
    import os
    if "VIRTUAL_ENV" in os.environ:
        with open(f"{os.environ['VIRTUAL_ENV']}/bin/activate", "a") as fa:
            fa.write(f)

class PostDevelopCommand(develop):
    """Post-installation for installation mode."""
    def run(self):
        develop.run(self)
        add2act()

class PostInstallCommand(install):
    """Post-installation for installation mode."""
    def run(self):
        install.run(self)
        add2act()

setup(
    name="turbokouros",
    version="0.0.1",
    author="okohulak",
    author_email="okohulak@sissa.it",
    description="Connector for Turbo-things",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://www.google.com/",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    #scripts=["src/bin/turbo-kouros"],
    python_requires=">=3.7",
    install_requires=[
          "argcomplete",
          "argparse",
          "paramiko",
          "pyyaml"
    ],
    entry_points = { "console_scripts":
                    ["turbo-kouros=turbokouros.turbokouros:main"] },
    cmdclass={
        'develop': PostDevelopCommand,
        'install': PostInstallCommand,
    },
)

