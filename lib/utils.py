import os
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
