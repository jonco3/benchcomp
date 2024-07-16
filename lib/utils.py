import os
import signal

# Attempt to navigate to root of mozilla source tree.
def chdir_to_source_root():
    lastDir = os.getcwd()
    while not os.path.isfile("client.mk") or \
          not os.path.isdir("mfbt") or \
          not os.path.isdir("js"):
        os.chdir("..")
        currentDir = os.getcwd()
        if currentDir == lastDir:
            sys.exit('Please run from within the mozilla source tree')
        lastDir = currentDir

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
