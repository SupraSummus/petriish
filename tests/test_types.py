from unittest import TestCase, skip
from petriish.types import Resolver, TypeResolutionError, PolymorphicType, Record, Bytes


class TypesTestCase(TestCase):
    def setUp(self):
        self.resolver = Resolver()

    def test_identity_bind(self):
        x = PolymorphicType()
        self.assertEqual(self.resolver.get_best_bind(x), x)

    def test_unify_with_self(self):
        x = PolymorphicType()
        self.resolver.unify(x, x)
        self.assertEqual(self.resolver.get_best_bind(x), x)

    def test_unify(self):
        x = PolymorphicType()
        self.resolver.unify(x, Bytes())
        self.assertEqual(self.resolver.get_best_bind(x), Bytes())

    def test_unify_in_record(self):
        x = PolymorphicType()
        y = PolymorphicType()
        self.resolver.unify(
            Record({'a': x, 'b': Record()}),
            Record({'a': Bytes(), 'b': y}),
        )
        self.assertEqual(self.resolver.get_best_bind(x), Bytes())
        self.assertEqual(self.resolver.get_best_bind(y), Record())

    def test_unify_two_variables(self):
        x = PolymorphicType()
        y = PolymorphicType()
        self.resolver.unify(x, y)
        self.assertEqual(self.resolver.get_best_bind(x), self.resolver.get_best_bind(y))
        self.assertIn(self.resolver.get_best_bind(x), [x, y])

    def test_reuse_resolver(self):
        x = PolymorphicType()
        y = PolymorphicType()
        self.resolver.unify(x, y)
        self.resolver.unify(y, Record())
        self.assertEqual(self.resolver.get_best_bind(x), Record())

    def test_recursive_type(self):
        x = PolymorphicType()
        y = PolymorphicType()
        self.resolver.unify(x, Record({'aaa': x}))
        self.resolver.unify(
            Record({'aaa': Record({'aaa': Record({'aaa': y})})}),
            Record({'aaa': x}),
        )
        self.assertEqual(self.resolver.get_best_bind(x), self.resolver.get_best_bind(y))

    @skip
    def test_fail_on_recursive_type(self):
        x = PolymorphicType()
        with self.assertRaises(TypeResolutionError):
            self.resolver.unify(x, Record({'aaa': x}))
        self.assertEqual(self.resolver.get_best_bind(x), x)

    def test_fail_on_reuse_resolver(self):
        x = PolymorphicType()
        self.resolver.unify(x, Record())
        with self.assertRaises(TypeResolutionError):
            self.resolver.unify(x, Bytes())
        self.assertEqual(self.resolver.get_best_bind(x), Record())
