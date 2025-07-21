import os
import signal
import sys

# Attempt to find the root of the mozilla source tree.
def path_to_source_root():
    path = '.'
    depth = 0
    while not os.path.isfile(os.path.join(path, "client.mk")) or \
          not os.path.isdir(os.path.join(path, "mfbt")) or \
          not os.path.isdir(os.path.join(path, "js")):
        path = os.path.join(path, '..')
        depth += 1
        if not os.path.isdir(path) or depth > 10:
            sys.exit('Please run from within the mozilla source tree')
    return os.path.normpath(path)

class DelayedKeyboardInterrupt(object):
    # From https://stackoverflow.com/a/21919644
    def __enter__(self):
        self.signal_received = False
        self.old_handler = signal.signal(signal.SIGINT, self.handler)

    def handler(self, sig, frame):
        self.signal_received = (sig, frame)

    def __exit__(self, type, value, traceback):
        signal.signal(signal.SIGINT, self.old_handler)
        if self.signal_received:
            self.old_handler(*self.signal_received)
