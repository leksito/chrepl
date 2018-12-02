import cmd
import readline
import os
from ismultiline import PushdownAutomata

historyfile = os.path.expanduser('~/.chromerepl_history')
historyfile_size = 1000

class Console(cmd.Cmd):

    prompt = ' > '

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_command = []

    def default(self, line):
        self.current_command.append(line)
        if PushdownAutomata().command_ends(line):
            print(PushdownAutomata().command_ends(line))
            self.prompt = ' > '
            print(''.join(self.current_command))
            self.current_command = []
        else:
            self.prompt = '...'
    
    def postcmd(self, stop, line):
        if line == 'exit':
            return True
        return False

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
    Console().cmdloop()

