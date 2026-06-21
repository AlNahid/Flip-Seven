import unittest
from rules_engine.cards import build_deck, Card, CardType, ModifierType, ActionType


class TestBuildDeck(unittest.TestCase):

    def setUp(self):
        # Runs fresh before every test method, so tests can't accidentally
        # affect each other by sharing one deck.
        self.deck = build_deck()

    def test_total_card_count(self):
        # 79 number + 6 modifier (1 of each, per your house rule) + 9 action
        self.assertEqual(len(self.deck), 94)

    def test_number_card_counts(self):
        number_cards = [c for c in self.deck if c.category == CardType.NUMBER]
        self.assertEqual(len(number_cards), 79)

        # There should be exactly one 0, exactly one 1, exactly two 2s, ...
        # exactly twelve 12s.
        for value in range(0, 13):
            count = sum(1 for c in number_cards if c.value == value)
            expected = 1 if value == 0 else value
            self.assertEqual(
                count, expected,
                f"expected {expected} copies of number {value}, found {count}"
            )

    def test_modifier_card_counts(self):
        modifier_cards = [c for c in self.deck if c.category == CardType.MODIFIER]
        self.assertEqual(len(modifier_cards), 6)

        # House rule: exactly one of each ModifierType, no duplicates.
        for modifier_type in ModifierType:
            count = sum(1 for c in modifier_cards if c.value == modifier_type)
            self.assertEqual(
                count, 1,
                f"expected exactly 1 of {modifier_type}, found {count}"
            )

    def test_action_card_counts(self):
        action_cards = [c for c in self.deck if c.category == CardType.ACTION]
        self.assertEqual(len(action_cards), 9)

        for action_type in ActionType:
            count = sum(1 for c in action_cards if c.value == action_type)
            self.assertEqual(
                count, 3,
                f"expected exactly 3 of {action_type}, found {count}"
            )

    def test_build_deck_returns_fresh_objects_each_call(self):
        # Guards against the "shared global list" bug discussed earlier:
        # two separate calls to build_deck() must not return the same
        # underlying list, or mutating one would silently mutate the other.
        deck_a = build_deck()
        deck_b = build_deck()
        self.assertIsNot(deck_a, deck_b)

        # Mutating one shouldn't affect the other.
        deck_a.pop()
        self.assertEqual(len(deck_a), 93)
        self.assertEqual(len(deck_b), 94)

    def test_card_fields_are_correct_types(self):
        for card in self.deck:
            self.assertIsInstance(card, Card)
            self.assertIsInstance(card.category, CardType)
            if card.category == CardType.NUMBER:
                self.assertIsInstance(card.value, int)
            elif card.category == CardType.MODIFIER:
                self.assertIsInstance(card.value, ModifierType)
            elif card.category == CardType.ACTION:
                self.assertIsInstance(card.value, ActionType)


if __name__ == "__main__":
    unittest.main()