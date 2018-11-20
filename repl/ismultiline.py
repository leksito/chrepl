class Stack(list):

    def pop(self):
        return super().pop() if len(self) > 0 else None

    def push(self, *args, **kwargs):
        super().append(*args, **kwargs)

    def last(self):
        return self[-1] if len(self) > 0 else None


class PushdownAutomata:

    brackets = [ "\"", "'", "[", "{", "(", ]
    reverse_brackets = [ "\"", "'", "]", "}", ")", ]

    def __init__(self):
        self.stack = Stack()

    def do_nothing(self):
        pass

    def terminals(self):
        return set(self.brackets) | set(self.reverse_brackets)

    def is_terminal(self, character):
        return character in self.terminals()

    def invert_terminal(self, terminal):
         return dict(zip(self.brackets, self.reverse_brackets))[terminal]

    def reverse_bracket(self, character):
        return self.stack.last() \
                and self.invert_terminal(self.stack.last()) == character

    def next_state(self, character):
        if character in self.brackets:
            self.stack.push(character)
        elif self.reverse_bracket(character):
            self.stack.pop()

    def command_ends(self, string):
        for character in string:
            pass
        return True
        

