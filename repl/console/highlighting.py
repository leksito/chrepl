import os, signal, ctypes, blessings, readline, sys, time, threading
#
from pygments import highlight
from pygments.formatters import TerminalFormatter
from pygments.lexers import JavascriptLexer

# terminal = blessings.Terminal()
# lexer = JavascriptLexer()
# formatter = TerminalFormatter()
#
# def slight_delay():
#     threading.Timer(0.001, draw).start()
#     return 0
#
# def draw():
#     raw_line = readline.get_line_buffer().replace("\n", "")
#     if len(raw_line) == 0:
#         return 0
#     line = highlight(raw_line, lexer, formatter)[:-1].replace("\n", "")
#
#     # print(line)
#     sys.stdout.write("\r" + ">>> " + line)
#     sys.stdout.flush()
#
#     readline.redisplay()
#     return 0
#
# def keyboard_interrupt(c, frame):   # Ctrl-C throws in C code otherwise
#     pass
#
# input_hook = ctypes.PYFUNCTYPE(ctypes.c_int)(draw)
# hook_ptr = ctypes.c_void_p.in_dll(ctypes.pythonapi,"PyOS_InputHook")
# hook_ptr.value = ctypes.cast(input_hook, ctypes.c_void_p).value
# signal.signal(signal.SIGINT, keyboard_interrupt)



def slight_delay():
    threading.Timer(0.001, draw).start()
    return 0

def draw():
    raw_line = readline.get_line_buffer()
    line = highlight(raw_line, lexer, formatter)[:-1]

    with lock:
        with terminal.location(x = 4):
            print line,
        readline.redisplay()

def keyboard_interrupt(c, frame):   # Ctrl-C throws in C code otherwise
    pass

callback = ctypes.PYFUNCTYPE(ctypes.c_int)(slight_delay)
hook_ptr = ctypes.c_void_p.in_dll(ctypes.pythonapi,"PyOS_InputHook")
hook_ptr.value = ctypes.cast(callback, ctypes.c_void_p).value
signal.signal(signal.SIGINT, keyboard_interrupt)

terminal = blessings.Terminal()
lexer = JavascriptLexer()
formatter = TerminalFormatter()
lock = threading.Lock()
