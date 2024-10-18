# -*- coding: utf-8 -*-

# A clearable display.

import ansi.cursor
import shutil

class Null:
    def print(self, text=''):
        pass

    def clear(self):
        pass

class Terminal:
    def __init__(self):
        self.reset()

    def print(self, text=''):
        if self.linesDisplayed + 1 >= self.height:
            return
        print(text[:self.width])
        self.linesDisplayed += 1

    def clear(self):
        for i in range(self.linesDisplayed):
            print(ansi.cursor.up() + ansi.cursor.erase_line(), end='')
        self.reset();

    def reset(self):
        (self.width, self.height) = shutil.get_terminal_size()
        self.linesDisplayed = 0

class File:
    def __init__(self, file):
        self.file = file

    def print(self, text=''):
        self.file.write(text + "\n")

    def clear(self):
        pass
