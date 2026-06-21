import unittest
from rules_engine.player import Player, PlayerState
from rules_engine.cards import Card, CardType, ModifierType, ActionType


def number_card(value: int) -> Card:
    return Card(CardType.NUMBER, value)


def modifier_card(modifier_type: ModifierType) -> Card:
    return Card(CardType.MODIFIER, modifier_type)


class TestPlayerInitialState(unittest.TestCase):

    def setUp(self):
        self.player = Player("Alice")

    def test_starts_active(self):
        self.assertTrue(self.player.is_active())
        self.assertFalse(self.player.is_busted())
        self.assertFalse(self.player.is_flipped())

    def test_starts_with_zero_scores(self):
        self.assertEqual(self.player.total_score, 0)
        self.assertEqual(self.player.round_score, 0)

    def test_starts_with_empty_hand(self):
        self.assertFalse(self.player.has_number_cards())
        self.assertFalse(self.player.has_modifier_cards())
        self.assertIsNone(self.player.second_chance_card)


class TestAddCards(unittest.TestCase):

    def setUp(self):
        self.player = Player("Alice")

    def test_add_number_card_appends_to_hand(self):
        self.player.add_number_card(number_card(5))
        self.assertEqual(len(self.player.number_cards), 1)
        self.assertTrue(self.player.has_number_cards())

    def test_add_number_card_rejects_non_number_card(self):
        with self.assertRaises(ValueError):
            self.player.add_number_card(modifier_card(ModifierType.PLUS_2))

    def test_add_modifier_card_appends_to_hand(self):
        self.player.add_modifier_card(modifier_card(ModifierType.PLUS_4))
        self.assertEqual(len(self.player.modifier_cards), 1)
        self.assertTrue(self.player.has_modifier_cards())

    def test_add_modifier_card_rejects_non_modifier_card(self):
        with self.assertRaises(ValueError):
            self.player.add_modifier_card(number_card(7))

    def test_add_number_card_does_not_duplicate_existing_cards(self):
        # Regression test for the "looping over number_cards and calling
        # add_number_card on each one" bug from earlier drafts -- adding
        # cards one at a time should never cause the hand to balloon.
        self.player.add_number_card(number_card(5))
        self.player.add_number_card(number_card(3))
        self.assertEqual(len(self.player.number_cards), 2)


class TestHasFlipSeven(unittest.TestCase):

    def setUp(self):
        self.player = Player("Alice")

    def test_false_with_fewer_than_seven_numbers(self):
        for v in [1, 2, 3]:
            self.player.add_number_card(number_card(v))
        self.assertFalse(self.player.has_flip_seven())

    def test_true_with_exactly_seven_numbers(self):
        for v in [1, 2, 3, 4, 5, 6, 7]:
            self.player.add_number_card(number_card(v))
        self.assertTrue(self.player.has_flip_seven())

    def test_sets_state_to_flipped_as_a_side_effect(self):
        # has_flip_seven() is documented (per our design discussion) to
        # both check AND set state -- this test locks in that contract.
        for v in [1, 2, 3, 4, 5, 6, 7]:
            self.player.add_number_card(number_card(v))
        self.assertFalse(self.player.is_flipped())  # not set yet
        self.player.has_flip_seven()
        self.assertTrue(self.player.is_flipped())  # now set


class TestRoundScoreNumbersOnly(unittest.TestCase):

    def test_sums_number_cards(self):
        player = Player("Alice")
        for v in [5, 3, 9]:
            player.add_number_card(number_card(v))
        self.assertEqual(player.get_round_score(), 17)

    def test_empty_hand_scores_zero(self):
        player = Player("Alice")
        self.assertEqual(player.get_round_score(), 0)

    def test_safe_to_call_multiple_times_in_a_row(self):
        # Regression test for the self.score / self.round_score
        # accumulation bugs from earlier drafts.
        player = Player("Alice")
        for v in [5, 3]:
            player.add_number_card(number_card(v))

        first_call = player.get_round_score()
        second_call = player.get_round_score()
        third_call = player.get_round_score()

        self.assertEqual(first_call, 8)
        self.assertEqual(second_call, 8)
        self.assertEqual(third_call, 8)
        # Hand itself should be untouched by scoring.
        self.assertEqual(len(player.number_cards), 2)


class TestRoundScoreWithModifiers(unittest.TestCase):

    def test_flat_modifier_adds_on_top_of_numbers(self):
        player = Player("Alice")
        player.add_number_card(number_card(10))
        player.add_modifier_card(modifier_card(ModifierType.PLUS_4))
        self.assertEqual(player.get_round_score(), 14)

    def test_times_2_doubles_number_sum_only(self):
        player = Player("Alice")
        player.add_number_card(number_card(10))
        player.add_modifier_card(modifier_card(ModifierType.TIMES_2))
        self.assertEqual(player.get_round_score(), 20)

    def test_times_2_and_flat_combined_numbers_then_double_then_flat(self):
        # This is the core order-of-operations bug from earlier drafts.
        # Spec: sum numbers -> apply x2 -> add flats.
        # numbers = 10, x2 -> 20, +4 flat -> 24 (NOT 28).
        player = Player("Alice")
        player.add_number_card(number_card(10))
        player.add_modifier_card(modifier_card(ModifierType.PLUS_4))
        player.add_modifier_card(modifier_card(ModifierType.TIMES_2))
        self.assertEqual(player.get_round_score(), 24)

    def test_order_of_modifier_card_arrival_does_not_change_score(self):
        # Same cards, opposite arrival order -- score must be identical.
        player_a = Player("A")
        player_a.add_number_card(number_card(10))
        player_a.add_modifier_card(modifier_card(ModifierType.PLUS_4))
        player_a.add_modifier_card(modifier_card(ModifierType.TIMES_2))

        player_b = Player("B")
        player_b.add_number_card(number_card(10))
        player_b.add_modifier_card(modifier_card(ModifierType.TIMES_2))
        player_b.add_modifier_card(modifier_card(ModifierType.PLUS_4))

        self.assertEqual(player_a.get_round_score(), player_b.get_round_score())

    def test_multiple_flat_modifiers_all_apply(self):
        player = Player("Alice")
        player.add_number_card(number_card(5))
        player.add_modifier_card(modifier_card(ModifierType.PLUS_2))
        player.add_modifier_card(modifier_card(ModifierType.PLUS_8))
        self.assertEqual(player.get_round_score(), 15)  # 5 + 2 + 8


class TestRoundScoreFlipSevenBonus(unittest.TestCase):

    def test_flip_seven_adds_fifteen(self):
        player = Player("Alice")
        for v in [1, 2, 3, 4, 5, 6, 7]:  # sums to 28
            player.add_number_card(number_card(v))
        self.assertEqual(player.get_round_score(), 28 + 15)

    def test_round_score_triggers_flip_seven_check_itself(self):
        # Regression test: round_score must call has_flip_seven() itself
        # rather than depending on something else having called it first.
        player = Player("Alice")
        for v in [1, 2, 3, 4, 5, 6, 7]:
            player.add_number_card(number_card(v))
        self.assertFalse(player.is_flipped())  # nobody's checked yet
        score = player.get_round_score()
        self.assertEqual(score, 28 + 15)  # bonus still applied correctly
        self.assertTrue(player.is_flipped())  # and state caught up


class TestRoundScoreBusted(unittest.TestCase):

    def test_busted_player_scores_zero_even_with_cards(self):
        player = Player("Alice")
        player.add_number_card(number_card(10))
        player.add_modifier_card(modifier_card(ModifierType.PLUS_8))
        player.state = PlayerState.BUSTED  # force state directly
        self.assertEqual(player.get_round_score(), 0)


class TestBustedDuplicateDetection(unittest.TestCase):
    """
    Known issue: Player.busted() uses set(self.number_cards) to detect
    duplicates. Card is a plain (non-frozen) dataclass, and plain
    dataclasses do not get a generated __hash__, so set() on a list of
    Cards raises TypeError. This test documents the current broken
    behavior so it fails clearly and specifically, rather than crashing
    the whole suite or failing somewhere confusing.

    Fix options to consider: make Card hashable (e.g. frozen=True),
    or rewrite busted() to compare card.value fields directly instead
    of relying on set() at all.
    """

    def test_busted_detects_duplicate_number_without_crashing(self):
        player = Player("Alice")
        player.add_number_card(number_card(7))
        player.add_number_card(number_card(7))  # duplicate
        try:
            result = player.busted()
        except TypeError as e:
            self.fail(
                "busted() raised TypeError -- Card is not hashable, so "
                f"set(self.number_cards) cannot work as written. ({e})"
            )
        self.assertTrue(result)
        self.assertTrue(player.is_busted())


class TestResetRound(unittest.TestCase):

    def test_clears_round_specific_fields(self):
        player = Player("Alice")
        player.add_number_card(number_card(5))
        player.add_modifier_card(modifier_card(ModifierType.PLUS_4))
        player.get_round_score()
        player.state = PlayerState.STAYED

        player.reset_round()

        self.assertEqual(player.number_cards, [])
        self.assertEqual(player.modifier_cards, [])
        self.assertIsNone(player.second_chance_card)
        self.assertEqual(player.round_score, 0)
        self.assertTrue(player.is_active())

    def test_does_not_touch_total_score_or_name(self):
        player = Player("Alice")
        player.add_number_card(number_card(5))
        player.get_round_score()
        player.get_total_score()  # banks 5 into total_score

        player.reset_round()

        self.assertEqual(player.total_score, 5)
        self.assertEqual(player.name, "Alice")


class TestGetTotalScore(unittest.TestCase):

    def test_adds_round_score_into_total(self):
        player = Player("Alice")
        player.add_number_card(number_card(5))
        player.get_round_score()  # round_score becomes 5
        self.assertEqual(player.get_total_score(), 5)

    def test_accumulates_across_multiple_rounds(self):
        player = Player("Alice")

        player.add_number_card(number_card(5))
        player.get_round_score()
        player.get_total_score()
        player.reset_round()

        player.add_number_card(number_card(9))
        player.get_round_score()
        player.get_total_score()

        self.assertEqual(player.total_score, 14)


if __name__ == "__main__":
    unittest.main()