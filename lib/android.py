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

# todo: improve copy test files

DestPath = "/data/local/tmp/"

def init(builds, tests, args):
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
        pushBinary(build, 'libnss3.so', path, True)

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

def pushBinary(build, binary, dstDir, skipIfMissing=False):
    print(f"Syncing {build.name} {binary}...")

    src = os.path.join(build.path, 'dist', 'bin', binary)
    if skipIfMissing and not os.path.isfile(src):
        return
    assert os.path.isfile(src)
    srcSum = runOrExit(['sha1sum', src])[0].splitlines()[0].split()[0];
    assert len(srcSum) == 40

    dst = f"{dstDir}/{binary}"
    dstSum = remoteShell(['sha1sum', dst, '||', 'echo', 'missing'])[0].split()[0];
    assert dstSum == 'missing' or len(dstSum) == 40

    if dstSum != srcSum:
        runOrExit(['adb', 'push', src, dst])

def runRemote(build, dir, command, env):
    env["LD_LIBRARY_PATH"] = DestPath + "build" + str(build.id)
    for key in env:
        command = [f"{key}={env[key]}"] + command
    command = ["cd", dir, "&&"] + command
    return remoteShell(command)

def getMaxCpuFrequency():
    out, _ = remoteShell(['cat', '/sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq'])
    freqs = map(int, out.splitlines())
    return max(freqs)

def getProfilePath():
    path = DestPath + "gcProfile.txt"
    remoteShell(['rm', '-f', path])
    return path

def readProfile(path):
    return remoteShell(['cat', path])[0]

def remoteShell(command):
    return runOrExit(['adb', 'shell'] + command)

def syncDir(src, dst):
    print(f"Syncing dir {src} to {dst}...")
    runOrExit(['adbsync', 'push', src, dst])

def runOrExit(command):
    p = subprocess.run(command, capture_output=True, text=True)
    if p.returncode != 0:
        sys.exit(f"Failed to run command:\n{' '.join(command)}: {p.stderr}")
    stdout = p.stdout.strip()
    stderr = p.stderr.strip()
    return stdout, stderr
