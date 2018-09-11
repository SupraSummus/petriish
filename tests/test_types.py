from unittest import TestCase
from petriish.types import Resolver, PolymorphicType, Record, Bytes


class TypesTestCase(TestCase):
    def setUp(self):
        self.resolver = Resolver()

    def test_unify(self):
        x = PolymorphicType()
        self.resolver.unify(x, Bytes())
        self.assertEqual(self.resolver._get_best_bind(x), Bytes())

    def test_unify_in_record(self):
        x = PolymorphicType()
        y = PolymorphicType()
        self.resolver.unify(
            Record({'a': x, 'b': Record()}),
            Record({'a': Bytes(), 'b': y}),
        )
        self.assertEqual(self.resolver._get_best_bind(x), Bytes())
        self.assertEqual(self.resolver._get_best_bind(y), Record())
