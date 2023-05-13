# -*- coding: utf-8 -*-

import os.path
import sys

class Test:
    def __init__(self, name, dir, script, args = []):
        self.name = name
        self.dir = dir
        self.script = script
        self.args = args

class OctaneTest(Test):
    def __init__(self, name, script=None):
        if not script:
            script = f"run-{name}.js"
        super().__init__(name, 'octane', script)

class LocalTest(Test):
    def __init__(self, spec):
        path, *args = spec.split(" ")
        path = os.path.normpath(os.path.expanduser(path))
        if not os.path.exists(path):
            sys.exit(f"Test '{path}' not found")

        dir, name = os.path.split(os.path.abspath(path))
        super().__init__(spec, dir, name, args)
