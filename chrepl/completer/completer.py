class Completer:

    def __init__(self):
        pass

    def complete(self, text, state):
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
