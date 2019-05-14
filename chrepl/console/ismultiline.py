import re
from functools import wraps

from chrepl.common.util import Singleton

class Stack(list):

    def pop(self):
        return super(Stack, self).pop() if len(self) > 0 else None

    def push(self, *args, **kwargs):
        super(Stack, self).append(*args, **kwargs)

    def last(self):
        return self[-1] if len(self) > 0 else None

    def empty(self):
        return len(self) == 0


class delete_nonterminals:

    def __init__(self, terminals):
        self.terminals = ''.join(terminals)

    def nonterminals_regex(self):
        return r"[^{}]+".format(re.escape(self.terminals))

    def reject_escape_characters(self, string):
        return re.sub( r"\\.", "", string)

    def reject_nonterminals(self, string):
        string = self.reject_escape_characters(string.strip())
        string = re.sub(self.nonterminals_regex(), "", string)
        return string

    def __call__(self, func):
        @wraps(func)
        def wrapper(this, *args, **kwargs):
            string = kwargs.get('string') or \
                    next((s for s in args if type(s) is str), None)
            return func(this, self.reject_nonterminals(string))
        return wrapper


class PushdownAutomata(Singleton):

    brackets = [ "\"", "'", "[", "{", "(", ]
    reverse_brackets = [ "\"", "'", "]", "}", ")", ]

    def __init__(self):
        self.stack = Stack()
        self.current_command = []

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
        if self.reverse_bracket(character):
            self.stack.pop()
        elif character in self.brackets:
            self.stack.push(character)

    @delete_nonterminals(set(brackets + reverse_brackets))
    def command_ends(self, line):
        for character in line:
            self.next_state(character)
        return self.stack.empty()
