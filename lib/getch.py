# Library to synchronously get a single key press.
#
# Based on examples from:
# https://stackoverflow.com/questions/13207678/whats-the-simplest-way-of-detecting-keyboard-input-in-a-script-from-the-termina

import platform
import sys

system = platform.system()
if system == 'Linux' or system == 'Darwin':
    import termios, fcntl, os
    isPosix = True
elif system == 'Windows':
    import msvcrt
    isPosix = False
else:
    sys.exit("Unsupported platform: " + system)

class KeyGetterWindows:
    def __enter__(self):
        return self

    def __exit__(self):
        pass

    def get(self):
        return msvcrt.getch()

class KeyGetterPosix:
    def __enter__(self):
        self.fd = sys.stdin.fileno()

        # Set terminal attributes.
        termattr = termios.tcgetattr(self.fd)
        self.oldattr = termattr.copy()
        termattr[3] &= ~termios.ICANON  # Disable canonical mode
        termattr[3] &= ~termios.ECHO  # Disable echo
        termios.tcsetattr(self.fd, termios.TCSANOW, termattr)

        return self

    def __exit__(self, type, value, traceback):
        # Restore terminal attributes and file descriptor flags.
        termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.oldattr)

    def get(self):
        return sys.stdin.read(1)

if isPosix:
    KeyGetter = KeyGetterPosix
else:
    KeyGetter = KeyGetterWindows
