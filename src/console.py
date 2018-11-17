import cmd
import readline
import os

historyfile = os.path.expanduser('~/.chromerepl_history')
historyfile_size = 1000

class Console(cmd.Cmd):

    prompt = ' > '

    def default(self, line):
        print(line)
    
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

