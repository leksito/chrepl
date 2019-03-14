import cmd
import readline
import os
from .ismultiline import PushdownAutomata

historyfile = os.path.expanduser('~/.chromerepl_history')
historyfile_size = 1000

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


if __name__ == '__main__':
    Cmd().cmdloop()
