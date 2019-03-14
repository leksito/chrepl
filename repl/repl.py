from console import Cmd


class Repl(Cmd):

    def __init__(self, *args, **kwargs):
        super(Repl, self).__init__(*args, **kwargs)

    def default(self, line):
        if self.command_ends():
           return self.process_command() 
        return False

    def process_command(self):
        command = self.get_command()
        print(command)
        return False



if __name__ == '__main__':
    Repl().cmdloop()
