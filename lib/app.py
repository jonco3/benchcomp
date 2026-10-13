# -*- coding: utf-8 -*-

# Textual application that displays benchmark results as they arrive.

import threading

from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Footer, Header, Static

class BenchApp(App):
    """
    Runs `work(report)` on a background thread. The work function calls
    `report(build, results)` for each benchmark run, which updates the display
    via `onResults(build, results)` (returns the lines to show) on the UI
    thread. `render()` returns the current lines and `onKey(args, key)` handles
    display option keys.
    """

    CSS = """
    VerticalScroll { overflow-x: auto; }
    #results { width: auto; }
    """

    BINDINGS = [
        ('q', 'quit', 'Quit'),
        ('c', "press('c')", 'Next compare'),
        ('C', "press('C')", 'Prev compare'),
        ('s', "press('s')", 'Summary'),
        ('l', "press('l')", 'Layout'),
        ('r', "press('r')", 'Reverse'),
        ('f', "press('f')", 'Significant only'),
    ]

    def __init__(self, args, work, onResults, render, onKey, onQuit):
        super().__init__()
        self.args = args
        self.work = work
        self.onResults = onResults
        self.render_lines = render
        self.onKey = onKey
        self.onQuit = onQuit
        self.error = None
        self.animation_level = 'none'  # Disable smooth scrolling.
        self.title = 'benchcomp'
        self.sub_title = 'Running'

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll():
            yield Static('', id='results', markup=False)
        yield Footer()

    def on_mount(self):
        threading.Thread(target=self.runWork, daemon=True).start()

    def runWork(self):
        try:
            self.work(self.report)
        except Exception as e:
            self.error = str(e)
        self.callUI(self.finished)

    def report(self, build, results):
        self.callUI(self.update, build, results)

    def callUI(self, fn, *args):
        try:
            self.call_from_thread(fn, *args)
        except RuntimeError:
            pass  # App has already exited.

    def update(self, build, results):
        self.show(self.onResults(build, results))

    def show(self, lines):
        self.query_one('#results', Static).update("\n".join(lines))

    def finished(self):
        if self.error:
            self.exit()
        else:
            self.sub_title = 'Finished'

    def action_press(self, key):
        self.onKey(self.args, key)
        self.show(self.render_lines())

    async def action_quit(self):
        self.onQuit()
        self.exit()
