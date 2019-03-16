import cmd
import readline
import os
from .ismultiline import PushdownAutomata

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

    def hook_ptr(self):
        if not hasattr(self, '_hook_ptr'):
            self._hook_ptr = ctypes.c_void_p.in_dll(ctypes.pythonapi,"PyOS_InputHook")
        return self._hook_ptr

    def enable_highlighting(self):
        terminal = blessings.Terminal()
        lexer = JavascriptLexer()
        formatter = TerminalFormatter()

        def draw():  
            raw_line = readline.get_line_buffer()
            line = highlight(raw_line, lexer, formatter)[:-1]

            with terminal.location(x = 4):
                print(line)
            readline.redisplay()
            return 0

        self.input_hook = ctypes.PYFUNCTYPE(ctypes.c_int)(draw)
        self.default_input_hook = self.hook_ptr.value
        self.hook_ptr.value = ctypes.cast(callback, ctypes.c_void_p).value

    def disable_highlighting(self):
        if hasattr(self, 'default_input_hook') and hasattr(self, 'hook_ptr'):
            self.hook_ptr.value = self.default_input_hook

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
            line = raw_input(self.prompt)
            lines.append(line)
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
            return
        finally:
            self.restore_completer()
