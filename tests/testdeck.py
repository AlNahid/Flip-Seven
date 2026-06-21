import unittest
from rules_engine.deck import Deck
from rules_engine.cards import Card, CardType


class TestDeck(unittest.TestCase):

    def setUp(self):
        self.deck = Deck()

    def test_starts_with_94_cards_in_draw_pile(self):
        self.assertEqual(len(self.deck.draw_pile), 94)
        self.assertEqual(self.deck.cards_remaining(), 94)

    def test_starts_with_empty_discard_pile(self):
        self.assertEqual(self.deck.discard_pile, [])

    def test_draw_card_removes_one_card_from_draw_pile(self):
        starting_count = self.deck.cards_remaining()
        card = self.deck.draw_card()

        self.assertIsInstance(card, Card)
        self.assertEqual(self.deck.cards_remaining(), starting_count - 1)

    def test_draw_card_returns_different_cards_over_multiple_draws(self):
        # Not a guarantee of randomness, just a sanity check that pop()
        # isn't somehow returning the same object repeatedly.
        drawn = [self.deck.draw_card() for _ in range(10)]
        self.assertEqual(len(drawn), 10)
        self.assertEqual(self.deck.cards_remaining(), 84)

    def test_shuffle_does_not_change_card_count(self):
        before = self.deck.cards_remaining()
        self.deck.shuffle()
        self.assertEqual(self.deck.cards_remaining(), before)

    def test_discard_card_adds_to_discard_pile(self):
        drawn_cards = [self.deck.draw_card() for _ in range(3)]
        self.deck.discard_card(drawn_cards)

        self.assertEqual(len(self.deck.discard_pile), 3)
        for card in drawn_cards:
            self.assertIn(card, self.deck.discard_pile)

    def test_draw_pile_does_not_shrink_from_discarding(self):
        # discard_card should only ever touch discard_pile, never draw_pile.
        before = self.deck.cards_remaining()
        drawn_cards = [self.deck.draw_card() for _ in range(3)]
        self.deck.discard_card(drawn_cards)

        # 3 fewer than the original 94, from the draws above -- discarding
        # those same 3 cards shouldn't remove anything further.
        self.assertEqual(self.deck.cards_remaining(), before - 3)

    def test_reshuffles_discard_pile_when_draw_pile_runs_out(self):
        # Drain the entire draw pile.
        all_cards = []
        while self.deck.cards_remaining() > 0:
            all_cards.append(self.deck.draw_card())

        self.assertEqual(len(all_cards), 94)
        self.assertEqual(self.deck.cards_remaining(), 0)

        # Put everything in the discard pile, simulating end-of-round cleanup.
        self.deck.discard_card(all_cards)
        self.assertEqual(len(self.deck.discard_pile), 94)

        # The deck is empty but the discard pile is full -- drawing now
        # should trigger a reshuffle rather than returning None.
        next_card = self.deck.draw_card()
        self.assertIsInstance(next_card, Card)

        # After reshuffling 94 cards in and immediately drawing 1,
        # draw_pile should have 93 left and discard_pile should be empty.
        self.assertEqual(self.deck.cards_remaining(), 93)
        self.assertEqual(len(self.deck.discard_pile), 0)

    def test_draw_card_returns_none_when_truly_empty(self):
        # Drain the draw pile and never refill the discard pile --
        # drawing again should return None rather than crashing.
        while self.deck.cards_remaining() > 0:
            self.deck.draw_card()

        self.assertEqual(self.deck.cards_remaining(), 0)
        self.assertEqual(self.deck.discard_pile, [])

        result = self.deck.draw_card()
        self.assertIsNone(result)

    def test_two_deck_instances_do_not_share_state(self):
        # Guards against accidentally sharing the same underlying list
        # between two separate Deck objects.
        deck_a = Deck()
        deck_b = Deck()

        deck_a.draw_card()
        self.assertEqual(deck_a.cards_remaining(), 93)
        self.assertEqual(deck_b.cards_remaining(), 94)


if __name__ == "__main__":
    unittest.main()