# -*- coding: utf-8 -*-

import os
import os.path
import sys
import utils

class Test:
    def __init__(self, name, kind):
        assert kind == 'shell' or kind == 'browser'
        self.name = name
        self.kind = kind

    def isShellTest(self):
        return self.kind == 'shell'

class ShellTest(Test):
    def __init__(self, name, dir, script, args=[]):
        if not os.path.isfile(os.path.join(dir, script)):
            sys.exit(f"Test script '${script}' not found in ${dir}")
        self.dir = dir
        self.script = script
        self.args = args
        super().__init__(name, 'shell')

class BrowserTest(Test):
    def __init__(self, name, args):
        self.args = args
        super().__init__(name, 'browser')

class OctaneTest(ShellTest):
    def __init__(self, name=None):
        if not name:
            name = 'octane'
            script = 'run.js'
        else:
            script = f"run-{name}.js"
        root = utils.path_to_source_root()
        dir = os.path.normpath(os.path.join(root, "js/src/octane"))
        super().__init__(name, dir, script)

class LocalTest(ShellTest):
    def __init__(self, spec):
        path, *args = spec.split(" ")
        path = os.path.normpath(os.path.expanduser(path))
        if not os.path.exists(path):
            sys.exit(f"Test '{path}' not found")
        dir, name = os.path.split(os.path.abspath(path))
        super().__init__(spec, dir, name, args)

class RaptorTest(BrowserTest):
    def __init__(self, name, testName=None):
        args = 'raptor --browsertime -t'.split()
        args.append(testName if testName else name)
        args.extend('--post-startup-delay 1000 --browser-cycles 1 --page-cycles 1'.split())
        super().__init__(name, args)

def getKnownTests():
    return [
        # Run all tests sequentially in a single runtime.
        OctaneTest(),

        # Run individual tests independently.
        OctaneTest('richards'),
        OctaneTest('deltablue'),
        OctaneTest('crypto'),
        OctaneTest('raytrace'),
        OctaneTest('earley-boyer'),
        OctaneTest('regexp'),
        OctaneTest('splay'),
        OctaneTest('navier-stokes'),
        OctaneTest('pdfjs'),
        OctaneTest('mandreel'),
        OctaneTest('gbemu'),
        OctaneTest('code-load'),
        OctaneTest('box2d'),
        OctaneTest('zlib'),
        OctaneTest('typescript'),

        # Browser tests
        RaptorTest('speedometer3'),
        RaptorTest('ares6'),
        RaptorTest('jetstream2'),
        RaptorTest('jetstream3', 'jetstream3-desktop'),
        RaptorTest('matrix-react-bench'),
        RaptorTest('speedometer', 'speedometer-desktop')
    ]
