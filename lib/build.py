# -*- coding: utf-8 -*-

import os.path
import sys

class Build:
    def __init__(self, spec):
        command = spec.split()
        path = os.path.expanduser(os.path.normpath(command[0]))
        shell = findShellInBuildDir(path)
        ensure(canExecute(shell), f"Shell not executable: {shell}")
        self.spec = spec
        self.path = path
        self.name = os.path.basename(self.path)
        self.shell = os.path.abspath(shell)
        self.args = command[1:]

    def __repr__(self):
        return f"Build({self.name})"

def findShellInBuildDir(path):
    locations = [['shell'],
                 ['dist', 'bin', 'shell'],
                 ['d8']]
    for location in locations:
        shell = os.path.join(path, *location)
        if os.path.isfile(shell):
            return shell

    sys.exit(f"No shell found under path: {path}")

def ensure(condition, error):
    if not condition:
        sys.exit(error)

def canExecute(path):
    return os.path.isfile(path) and os.access(path, os.X_OK)
