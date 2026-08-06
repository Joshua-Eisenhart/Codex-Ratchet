import unittest

from mymod import normalise, parse


class T(unittest.TestCase):
    def test_variable_call(self):
        got = normalise([1, 2, 3])
        self.assertEqual(got, [0.0, 0.5, 1.0])

    def test_call_vs_literal(self):
        self.assertEqual(normalise([1, 2]), [0.0, 1.0])

    def test_call_vs_call(self):
        self.assertEqual(parse("a"), normalise("a"))

    def test_const_arg_call(self):
        self.assertEqual(sum([1, 2, 3]), 6)
