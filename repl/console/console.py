import cmd, readline, os, signal

from .ismultiline import PushdownAutomata
import highlighting

import code, ctypes, readline, blessings
from pygments import highlight
from pygments.formatters import TerminalFormatter
from pygments.lexers import JavascriptLexer

historyfile = os.path.expanduser('~/.chromerepl_history')
historyfile_size = 1000

PROMPT = '>>> '
MLINE_PROMPT = '... '
INTRO = """
Intro
"""

def keyboard_interrupt(c, frame):
    return

signal.signal(signal.SIGINT, keyboard_interrupt)


class Cmd:

    def __init__(self, completer=None, completekey='tab'):
        self.prompt = PROMPT
        self.intro = INTRO
        if completer:
            self.set_completer(completer, completekey)
        else:
            self.set_completer(self.default_completer, completekey)
        self.configure_command_history()
        self.save_command_history_to_file()

        # Highlighting().enable()

    def default_completer(self, text, state):
        if state == 0:
            default_names = [
                    'var', 'function',  'function2', 'console'
                    ]
            if not text:
                self.matches = default_names[:]
            else:
                self.matches = [name for name in default_names if name.startswith(text)]
        try:
            return self.matches[state]
        except IndexError:
            return None

    def configure_command_history(self):
        if readline and os.path.exists(historyfile):
            readline.read_history_file(historyfile)

    def save_command_history_to_file(self):
        if readline:
            readline.set_history_length(historyfile_size)
            readline.write_history_file(historyfile)

    def set_completer(self, completer, completekey):
        self.old_completer = readline.get_completer()
        readline.set_completer(completer)
        readline.parse_and_bind(completekey+":complete")

    def restore_completer(self):
        if hasattr(self, 'old_completer'):
            readline.set_completer(self.old_completer)

    def get_command(self):
        lines = []
        readline.set_startup_hook()
        while True:
            try:
                line = raw_input(self.prompt)
                lines.append(line)
            except EOFError:
                print("\n")
                exit(0)
            if PushdownAutomata().command_ends(line):
                self.prompt = PROMPT
                return '\n'.join(lines)
            else:
                self.prompt = MLINE_PROMPT
            indentation = " " * 4 * len(PushdownAutomata().stack)
            readline.set_startup_hook(lambda: readline.insert_text(indentation))

    def cmd_generator(self):
        try:
            print(self.intro)
            while True:
                yield self.get_command()
        except KeyboardInterrupt:
            self.disable_highlighting()
            return
        finally:
            self.restore_completer()
