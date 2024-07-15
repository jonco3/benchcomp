import os

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
