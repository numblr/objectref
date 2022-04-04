import unittest

from cltl.eliza.eliza import ElizaImpl, GREETING


class TestEliza(unittest.TestCase):
    def setUp(self) -> None:
        self.eliza = ElizaImpl()

    def test_greeting(self):
        self.assertEqual(GREETING, self.eliza.respond(None))
        self.assertNotEqual(GREETING, self.eliza.respond(None))

    def test_response(self):
        response = self.eliza.respond("I have problems with my relationship")
        self.assertRegex(response, "relationship")