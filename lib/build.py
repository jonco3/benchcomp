# -*- coding: utf-8 -*-

import json
import os.path
import platform
import sys

serial = 1

class Build:
    def __init__(self, spec):
        command = spec.split()
        path = os.path.expanduser(os.path.normpath(command[0]))
        shell = findShellForPath(path)
        browserConfig = getBrowserConfigForPath(path)
        if not shell and not browserConfig:
            sys.exit(f"No shell or browser found under path: {path}")

        self.spec = spec
        self.path = path
        self.name = os.path.basename(self.path)
        self.shell = shell
        self.browserConfig = browserConfig
        self.args = command[1:]
        global serial
        self.id = serial
        serial += 1

    def __repr__(self):
        return f"Build({self.name})"

    def hasShell(self):
        return self.shell != None

    def hasBrowser(self):
        return self.browserConfig != None

def findShellForPath(path):
    if os.path.isfile(path):
        return path

    locations = [['shell'], ['dist', 'bin', 'js'], ['d8'], ['bin', 'jsc']]
    for location in locations:
        shell = os.path.join(path, *location)
        if platform.system() == 'Windows':
            shell += '.exe'
        if os.path.exists(shell) and os.access(shell, os.X_OK):
            return os.path.abspath(shell)

    return None

def getBrowserConfigForPath(path):
    browser = os.path.join(path, 'dist/bin/firefox')
    if platform.system() == 'Windows':
        browser += '.exe'
    if not os.path.exists(browser) or not os.access(browser, os.X_OK):
        return None

    mozinfo = os.path.join(path, 'mozinfo.json')
    if not os.path.exists(mozinfo):
        return None

    with open(mozinfo) as f:
        info = json.load(f)

    assert 'mozconfig' in info
    return info['mozconfig']
