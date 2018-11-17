import cmd
import readline
import os

historyfile = os.path.expanduser('~/.chromerepl_history')
historyfile_size = 1000

class Console(cmd.Cmd):

    prompt = ' > '

    def default(self, line):
        print(line)
        return True

    def preloop(self):
        if readline and os.path.exists(historyfile):
            readline.read_history_file(historyfile)

    def postloop(self):
        if readline:
            readline.set_history_length(historyfile_size)
            readline.write_history_file(historyfile)

    def postcmd(self, stop, line):
        print(stop, line)
        return False

Console().cmdloop()

