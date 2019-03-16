import cmd
import readline
import os
from .ismultiline import PushdownAutomata

historyfile = os.path.expanduser('~/.chromerepl_history')
historyfile_size = 1000

PROMPT = ' >>> '
MLINE_PROMPT = ' ... '
INTRO = """
Intro
"""

class Cmd2:

    def __init__(self, completer=None, completekey='tab'):
        self.prompt = PROMPT
        self.intro = INTRO
        if completer:
            self.set_completer(completer, completekey)
        else:
            self.set_completer(self.default_completer, completekey)
        self.configure_command_history()
        self.save_command_history_to_file()

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
        while True:
            line = input(self.prompt)
            lines.append(line)
            if PushdownAutomata().command_ends(line):
                self.prompt = PROMPT
                return '\n'.join(lines)
            else:
                self.prompt = MLINE_PROMPT

    def cmd_generator(self):
        try:
            print(self.intro)
            while True:
                yield self.get_command()
        except KeyboardInterrupt:
            return
        finally:
            self.restore_completer()




class Cmd(cmd.Cmd):

    prompt = ' > '

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.command_lines = []
        self._command_ends = True

    def postcmd(self, stop, line):
        self.command_lines.append(line)
        if PushdownAutomata().command_ends(line):
            self.command_lines = []
            self.command_ended
        else:
            self._command_ends = False
        self.prompt = ' > ' if self.is_command_ends() else '...'
        return False

    def end_command(self):
        self._command_ends = True

    def end_command(self):
        self._command_ends = False

    def is_command_ended(self):
        return self._command_ends

    def default(self, line):
        pass

    def get_command(self):
        return '\n'.join(self.command_lines)

    def configure_command_history(self):
        if readline and os.path.exists(historyfile):
            readline.read_history_file(historyfile)

    def save_command_history_to_file(self):
        if readline:
            readline.set_history_length(historyfile_size)
            readline.write_history_file(historyfile)

    def preloop(self):
        self.configure_command_history()

    def postloop(self):
        self.save_command_history_to_file()

