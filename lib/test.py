# -*- coding: utf-8 -*-

import os
import os.path
import re
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
    def __init__(self, root, name=None):
        if not name:
            name = 'octane'
            script = 'run.js'
        else:
            script = f"run-{name}.js"
        dir = os.path.normpath(os.path.join(root, "js/src/octane"))
        super().__init__(name, dir, script)

class SunspiderTest(ShellTest):
    def __init__(self, root):
        name = 'sunspider'
        script = 'sunspider-standalone-driver.js'
        dir = 'third_party/webkit/PerformanceTests/SunSpider/sunspider-0.9.1'
        dir = os.path.normpath(os.path.join(root, dir))
        super().__init__(name, dir, script)

class SixSpeedTest(ShellTest):
    def __init__(self, root):
        name = 'six-speed'
        script = 'test.js'
        dir = 'third_party/webkit/PerformanceTests/six-speed'
        dir = os.path.normpath(os.path.join(root, dir))
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
    def __init__(self, name, testName=None, urlParams=None):
        args = ['-t', testName if testName else name]
        if urlParams:
            args.extend(['--test-url-params', urlParams])
        args.extend(
            '--post-startup-delay 1000 --browser-cycles 1 --page-cycles 1'.
            split())
        super().__init__(name, args)

def getOctaneSubtests(root):
    dir = os.path.join(root, "js/src/octane")
    names = []
    for file in sorted(os.listdir(dir)):
        if file.startswith('run-') and file.endswith('.js'):
            names.append(file[len('run-'):-len('.js')])
    return names

def getSpeedometer3Subtests(root):
    path = os.path.join(root, "third_party/webkit/PerformanceTests",
                        "Speedometer3/resources/tests.mjs")
    names = []
    with open(path) as f:
        for line in f:
            # Suite names are the top-level 'name' properties in the Suites
            # array.
            match = re.match(r'^\s+name:\s+"([^"]+)",', line)
            if match:
                names.append(match.group(1))
    return names

def getJetStream3Subtests():
    # Raptor clones JetStream into the mozbuild state directory the first time
    # a jetstream3 test is run. If that hasn't happened yet there are no
    # subtests to list.
    state = os.environ.get('MOZBUILD_STATE_PATH',
                           os.path.expanduser('~/.mozbuild'))
    path = os.path.join(state, 'performance-tests/jetstream/JetStreamDriver.js')
    if not os.path.isfile(path):
        return []

    names = []
    inWtbTests = False
    with open(path) as f:
        for line in f:
            # Benchmarks and groups are registered with a literal name.
            match = re.match(r'^\s+name: "([^"]+)",', line)
            if match:
                names.append(match.group(1))
                continue

            # Web tooling benchmarks are generated from a table of names.
            if line.startswith('const WTB_TESTS = {'):
                inWtbTests = True
            elif inWtbTests:
                if line.startswith('}'):
                    inWtbTests = False
                    continue
                match = re.match(r'^\s+"([^"]+)":', line)
                if match:
                    names.append(f"{match.group(1)}-wtb")
    return names

def getKnownTests():
    tests = []

    # Finding some tests requires being in a Mozilla checkout.
    root = utils.path_to_source_root()

    if root:
        # Run all octane tests sequentially in a single runtime.
        tests.append(OctaneTest(root))

        # Run octane individual tests independently.
        for name in getOctaneSubtests(root):
            tests.append(OctaneTest(root, name))

        tests.append(SunspiderTest(root))
        tests.append(SixSpeedTest(root))

    tests.append(RaptorTest('speedometer3'))
    if root:
        for name in getSpeedometer3Subtests(root):
            tests.append(RaptorTest(f"speedometer3-{name}", 'speedometer3', f"suite={name}"))

    tests.append(RaptorTest('ares6'))
    tests.append(RaptorTest('jetstream2'))

    tests.append(RaptorTest('jetstream3', 'jetstream3-desktop'))
    for name in getJetStream3Subtests():
        tests.append(RaptorTest(f"jetstream3-{name}", 'jetstream3-desktop', f"test={name}"))

    tests.append(RaptorTest('matrix-react-bench'))
    tests.append(RaptorTest('speedometer', 'speedometer-desktop'))

    return tests
