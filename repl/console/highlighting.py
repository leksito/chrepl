import os, signal, ctypes, blessings, readline

from .util import Singleton

from pygments import highlight
from pygments.formatters import TerminalFormatter
from pygments.lexers import JavascriptLexer

class Highlighting(Singleton):

    def __init__(self):
        self.terminal = blessings.Terminal()
        self.lexer = JavascriptLexer()
        self.formatter = TerminalFormatter()

        hook_ptr = ctypes.c_void_p.in_dll(ctypes.pythonapi,"PyOS_InputHook")
        input_hook = ctypes.PYFUNCTYPE(ctypes.c_int)(self.draw)
        hook_ptr.value = ctypes.cast(input_hook, ctypes.c_void_p).value

    def draw(self):  
        if hasattr(self, 'highlighting') and self.highlighting:
            raw_line = readline.get_line_buffer()
            line = highlight(raw_line, self.lexer, self.formatter)[:-1]

            with self.terminal.location(x = 4):
                print(line)
            readline.redisplay()
        return 0

    def enable(self):
        self.highlighting = True

    def disable(self):
        self.highlighting = False
