import unittest
from repl import ismultiline

class TestTest(unittest.TestCase):
    def setUp(self):
        self.automata = ismultiline.PushdownAutomata()

    def test_pop_from_stack(self):
        self.automata.stack.push(1)
        self.assertEqual(self.automata.stack.pop(), 1,
                'result of pop method must be 1')
        self.assertEqual(len(self.automata.stack), 0,
                'stack length must be 0')
        self.assertEqual(self.automata.stack.pop(), None,
                'result of pop method must be None')

    def test_last_element_in_stack(self):
        self.assertEqual(self.automata.stack.last(), None,
                'last element must be None')
        self.automata.stack.push(1)
        self.assertEqual(self.automata.stack.last(), 1,
                'last element must be 1')

    def test_is_terminal(self):
        self.assertTrue(self.automata.is_terminal("\""))
        self.assertTrue(self.automata.is_terminal("'"))
        self.assertTrue(self.automata.is_terminal("["))
        self.assertTrue(self.automata.is_terminal("}"))
    
    def test_invert_terminal(self):
        self.assertEqual(self.automata.invert_terminal("["), "]")
        self.assertEqual(self.automata.invert_terminal("\""), "\"")
        self.assertEqual(self.automata.invert_terminal("("), ")")

    def test_reverse_bracket(self):
        self.automata.stack.push("[")
        self.assertTrue(self.automata.reverse_bracket("]"))
        self.automata.stack.push("\"")
        self.assertTrue(self.automata.reverse_bracket("\""))
        self.automata.stack.pop()
        self.automata.stack.pop()
        self.assertFalse(self.automata.reverse_bracket("\""))

    def test_next_state(self):
        result = self.automata.next_state("a")
        self.assertListEqual(self.automata.stack, [])

        result = self.automata.next_state("[")
        self.assertListEqual(self.automata.stack, ["["])

        result = self.automata.next_state("}")
        self.assertListEqual(self.automata.stack, ["["])

        result = self.automata.next_state("]")
        self.assertListEqual(self.automata.stack, [])
