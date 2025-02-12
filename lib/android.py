# -*- coding: utf-8 -*-

# Requires adb and adbsync (install with: pip install BetterADBSync)

# To do:
#  - currently only supports octane; for other tests we need to know
#    which test files to copy
#  - support GC profile

import os.path
import subprocess
import sys

from test import OctaneTest

# todo: how to get test files across?
#  - for octane it's two files and we can copy these
#  - use adbsync (pip install BetterADBSync)

DestPath = "/data/local/tmp/"

def initAndroid(builds, tests, args):
    if args.gc_profile:
        sys.exit("Not implemented for Android: --gc-profile")
    if args.sys_usage:
        sys.exit("Not implemented for Android: --sys-usage")
    if args.perf:
        sys.exit("Not implemented for Android: --perf")
    if args.numa:
        sys.exit("Not implemented for Android: --numa")

    # Check we can run adb and adbsync
    runOrExit(['adb', 'version'])
    runOrExit(['adbsync', '--version'])

    # Check there's a device attached
    devices = runOrExit(['adb', 'devices'])[0].splitlines()
    assert devices[0] == "List of devices attached"
    devices.pop(0)
    if len(devices) != 1:
        sys.exit("Expected one Android device attached but saw: " +
                 ", ".join(devices))

    # Copy the binaries for each build to their own directory on device
    for build in builds:
        if not os.path.isdir(os.path.join(build.path, "dist", "bin")):
            sys.exit(
                "Pass path to base of build directory for use with Android")

        name = "build" + str(build.id)
        path = DestPath + name
        remoteShell(["mkdir", "-p", path])  # how to check success?

        pushBinary(build, 'js', path)
        pushBinary(build, 'libmozglue.so', path)
        pushBinary(build, 'libnss3.so', path)

        # Update shell attribute to the Android-local path
        build.shell = path + "/js"

    # Copy test files to the device
    for test in tests:
        if not isinstance(test, OctaneTest):
            sys.exit("Only octane tests supported on Android for now")

        path = DestPath + "test/octane"
        syncDir(test.dir, path)

        # Update dir attribute to the Android-local path
        test.dir = path

def runRemote(build, dir, command, env):
    env["LD_LIBRARY_PATH"] = DestPath + "build" + str(build.id)
    for key in env:
        command = [f"{key}={env[key]}"] + command
    command = ["cd", dir, "&&"] + command
    return remoteShell(command)

def remoteShell(command):
    return runOrExit(['adb', 'shell'] + command)

def pushBinary(build, name, path):
    print(f"Syncing {build.name} {name}...")
    src = os.path.join(build.path, 'dist', 'bin', name)
    runOrExit(['adb', 'push', '--sync', src, path])

def syncDir(src, dst):
    print(f"Syncing dir {src} to {dst}...")
    runOrExit(['adbsync', 'push', src, dst])

def runOrExit(command):
    #print(f"runOrExit {' '.join(command)}")
    p = subprocess.run(command, capture_output=True, text=True)
    if p.returncode != 0:
        sys.exit(f"Failed to run command:\n{' '.join(command)}: {p.stderr}")
    stdout = p.stdout.strip()
    stderr = p.stderr.strip()
    #if stdout:
    #    print(stdout)
    #if stderr:
    #    print(stderr)
    #print('---')
    return stdout, stderr
