# -*- coding: utf-8 -*-

import os
import os.path
import sys
import utils

class Test:
    def __init__(self, name, dir, script, args=[]):
        self.name = name
        self.dir = dir
        self.script = script
        self.args = args
        if not os.path.isfile(os.path.join(dir, script)):
            sys.exit(f"Test script '${script}' not found in ${dir}")

class OctaneTest(Test):
    def __init__(self, name=None):
        if not name:
            name = 'octane'
            script = 'run.js'
        else:
            script = f"run-{name}.js"
        utils.chdir_to_source_root()
        dir = "js/src/octane"
        super().__init__(name, dir, script)

class LocalTest(Test):
    def __init__(self, spec):
        path, *args = spec.split(" ")
        path = os.path.normpath(os.path.expanduser(path))
        if not os.path.exists(path):
            sys.exit(f"Test '{path}' not found")

        dir, name = os.path.split(os.path.abspath(path))
        super().__init__(spec, dir, name, args)
