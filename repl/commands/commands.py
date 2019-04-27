
class Command: pass

class FirstCommand(Command): 
    regexp = r'^break .+'

class TestCommand(Command): pass
    regexp = r'^continue'

class CommandFactory:

    def __init__(self):
        pass

    @staticmethod
    def factory(command):

        list(map(lambda x: x.__name__, Command.__subclasses__()))
