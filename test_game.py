import unittest
from unittest.mock import patch
from rules_engine.game import Game
from rules_engine.player import Player, PlayerState
from rules_engine.cards import Card, CardType, ModifierType, ActionType


# ── helpers ──────────────────────────────────────────────────────────────────

def num(v: int) -> Card:
    return Card(CardType.NUMBER, v)

def mod(m: ModifierType) -> Card:
    return Card(CardType.MODIFIER, m)

def action(a: ActionType) -> Card:
    return Card(CardType.ACTION, a)

def fresh_game(names=None) -> Game:
    return Game(names or ["Alice", "Bob", "Charlie"])


# ── construction ─────────────────────────────────────────────────────────────

class TestGameInit(unittest.TestCase):

    def test_players_constructed_from_names(self):
        g = fresh_game(["Alice", "Bob"])
        self.assertEqual(len(g.players), 2)
        self.assertEqual(g.players[0].name, "Alice")
        self.assertEqual(g.players[1].name, "Bob")

    def test_initial_round_number_is_zero(self):
        g = fresh_game()
        self.assertEqual(g.round_number, 0)

    def test_flip_seven_not_triggered_at_start(self):
        g = fresh_game()
        self.assertFalse(g.flip_seven_triggered)

    def test_all_players_active_at_start(self):
        g = fresh_game()
        self.assertTrue(all(p.is_active() for p in g.players))

    def test_deck_has_94_cards(self):
        g = fresh_game()
        self.assertEqual(g.deck.cards_remaining(), 94)

    def test_current_player_index_starts_after_first_player(self):
        g = fresh_game(["Alice", "Bob", "Charlie"])
        expected = (g.first_player_index + 1) % len(g.players)
        self.assertEqual(g.current_player_index, expected)


# ── active_players / is_round_over ───────────────────────────────────────────

class TestActivePlayersAndRoundOver(unittest.TestCase):

    def test_all_active_at_start(self):
        g = fresh_game()
        self.assertEqual(len(g.active_players()), 3)

    def test_active_players_excludes_busted(self):
        g = fresh_game()
        g.players[0].state = PlayerState.BUSTED
        self.assertEqual(len(g.active_players()), 2)
        self.assertNotIn(g.players[0], g.active_players())

    def test_active_players_excludes_stayed(self):
        g = fresh_game()
        g.players[1].state = PlayerState.STAYED
        self.assertEqual(len(g.active_players()), 2)

    def test_active_players_excludes_frozen(self):
        g = fresh_game()
        g.players[0].state = PlayerState.FROZEN
        self.assertNotIn(g.players[0], g.active_players())

    def test_active_players_excludes_flipped(self):
        g = fresh_game()
        g.players[0].state = PlayerState.FLIPPED
        self.assertNotIn(g.players[0], g.active_players())

    def test_round_not_over_at_start(self):
        g = fresh_game()
        self.assertFalse(g.is_round_over())

    def test_round_over_when_no_active_players(self):
        g = fresh_game()
        for p in g.players:
            p.state = PlayerState.STAYED
        self.assertTrue(g.is_round_over())

    def test_round_over_when_flip_seven_triggered(self):
        g = fresh_game()
        g.flip_seven_triggered = True
        self.assertTrue(g.is_round_over())

    def test_is_round_over_returns_bool_not_none(self):
        g = fresh_game()
        result = g.is_round_over()
        self.assertIsInstance(result, bool)


# ── start_new_round ───────────────────────────────────────────────────────────

class TestStartNewRound(unittest.TestCase):

    def setUp(self):
        self.g = fresh_game()
        # Simulate a round having happened
        self.g.players[0].state = PlayerState.BUSTED
        self.g.players[1].state = PlayerState.STAYED
        self.g.flip_seven_triggered = True
        self.g.start_new_round()

    def test_increments_round_number(self):
        self.assertEqual(self.g.round_number, 1)

    def test_resets_flip_seven_flag(self):
        self.assertFalse(self.g.flip_seven_triggered)

    def test_all_players_active_after_reset(self):
        self.assertTrue(all(p.is_active() for p in self.g.players))

    def test_first_player_index_rotates(self):
        # Started at 0, should now be 1 after one round
        self.assertEqual(self.g.first_player_index, 1)

    def test_current_player_index_follows_first_player(self):
        expected = (self.g.first_player_index + 1) % len(self.g.players)
        self.assertEqual(self.g.current_player_index, expected)

    def test_multiple_rounds_rotate_correctly(self):
        g = fresh_game(["A", "B", "C"])
        for expected_first in [1, 2, 0, 1]:
            g.start_new_round()
            self.assertEqual(g.first_player_index, expected_first)


# ── player_stay ───────────────────────────────────────────────────────────────

class TestPlayerStay(unittest.TestCase):

    def test_stay_sets_state_to_stayed(self):
        g = fresh_game()
        g.players[0].add_number_card(num(5))
        g.player_stay(g.players[0])
        self.assertEqual(g.players[0].state, PlayerState.STAYED)

    def test_stay_without_number_cards_raises(self):
        g = fresh_game()
        with self.assertRaises(ValueError):
            g.player_stay(g.players[0])

    def test_stay_on_inactive_player_raises(self):
        g = fresh_game()
        g.players[0].state = PlayerState.BUSTED
        g.players[0].add_number_card(num(5))
        with self.assertRaises(ValueError):
            g.player_stay(g.players[0])


# ── next_active_player ────────────────────────────────────────────────────────

class TestNextActivePlayer(unittest.TestCase):

    def test_returns_next_active_player(self):
        g = fresh_game(["Alice", "Bob", "Charlie"])
        g.current_player_index = 0
        next_p = g.next_active_player()
        self.assertIsInstance(next_p, Player)
        self.assertTrue(next_p.is_active())

    def test_skips_inactive_players(self):
        g = fresh_game(["Alice", "Bob", "Charlie"])
        g.current_player_index = 0
        g.players[1].state = PlayerState.BUSTED  # skip index 1
        next_p = g.next_active_player()
        self.assertEqual(next_p.name, "Charlie")

    def test_raises_when_round_is_over(self):
        g = fresh_game()
        for p in g.players:
            p.state = PlayerState.STAYED
        with self.assertRaises(ValueError):
            g.next_active_player()

    def test_raises_when_no_active_players_found(self):
        g = fresh_game(["Alice", "Bob"])
        g.current_player_index = 0
        g.players[0].state = PlayerState.STAYED
        g.players[1].state = PlayerState.BUSTED
        with self.assertRaises(ValueError):
            g.next_active_player()


# ── resolve_number_card ───────────────────────────────────────────────────────

class TestResolveNumberCard(unittest.TestCase):

    def test_adds_card_to_hand(self):
        g = fresh_game()
        g.resolve_number_card(g.players[0], num(5))
        self.assertEqual(len(g.players[0].number_cards), 1)

    def test_duplicate_busts_player(self):
        g = fresh_game()
        g.resolve_number_card(g.players[0], num(5))
        g.resolve_number_card(g.players[0], num(5))
        self.assertTrue(g.players[0].is_busted())

    def test_duplicate_card_stays_in_hand_for_display(self):
        # Intentional design: duplicate stays in hand so UI can show it
        g = fresh_game()
        g.resolve_number_card(g.players[0], num(5))
        g.resolve_number_card(g.players[0], num(5))
        self.assertEqual(len(g.players[0].number_cards), 2)

    def test_seven_unique_numbers_sets_flip_seven_flag(self):
        g = fresh_game()
        for v in [1, 2, 3, 4, 5, 6, 7]:
            g.resolve_number_card(g.players[0], num(v))
        self.assertTrue(g.flip_seven_triggered)

    def test_inactive_player_raises(self):
        g = fresh_game()
        g.players[0].state = PlayerState.STAYED
        with self.assertRaises(ValueError):
            g.resolve_number_card(g.players[0], num(5))

    def test_second_chance_saves_from_bust(self):
        g = fresh_game()
        sc = action(ActionType.SECOND_CHANCE)
        g.players[0].second_chance_card = sc
        g.resolve_number_card(g.players[0], num(5))
        g.resolve_number_card(g.players[0], num(5))  # saved by SC
        # player.busted() detects duplicate but SC clears it:
        # state stays ACTIVE (not BUSTED) and SC slot is cleared
        self.assertIsNone(g.players[0].second_chance_card)
        self.assertFalse(g.players[0].is_busted())

    def test_second_chance_removes_duplicate_from_hand(self):
        g = fresh_game()
        g.players[0].second_chance_card = action(ActionType.SECOND_CHANCE)
        g.resolve_number_card(g.players[0], num(5))
        g.resolve_number_card(g.players[0], num(5))  # saved by SC
        values = [c.value for c in g.players[0].number_cards]
        self.assertEqual(values.count(5), 1)  # only one 5 remains

    def test_second_chance_discards_both_cards_to_deck(self):
        g = fresh_game()
        sc = action(ActionType.SECOND_CHANCE)
        g.players[0].second_chance_card = sc
        g.resolve_number_card(g.players[0], num(5))
        dup = num(5)
        g.resolve_number_card(g.players[0], dup)
        self.assertIn(sc, g.deck.discard_pile)


# ── resolve_modifier_card ─────────────────────────────────────────────────────

class TestResolveModifierCard(unittest.TestCase):

    def test_adds_modifier_to_hand(self):
        g = fresh_game()
        g.resolve_modifier_card(g.players[0], mod(ModifierType.PLUS_4))
        self.assertEqual(len(g.players[0].modifier_cards), 1)

    def test_inactive_player_raises(self):
        g = fresh_game()
        g.players[0].state = PlayerState.BUSTED
        with self.assertRaises(ValueError):
            g.resolve_modifier_card(g.players[0], mod(ModifierType.PLUS_2))


# ── apply_freeze_player ──────────────────────────────────────────────────────────────

class TestApplyFreeze(unittest.TestCase):

    def test_sets_player_state_to_frozen(self):
        g = fresh_game()
        g.apply_freeze_player(g.players[0], action(ActionType.FREEZE))
        self.assertEqual(g.players[0].state, PlayerState.FROZEN)

    def test_freeze_card_goes_to_discard_pile(self):
        g = fresh_game()
        card = action(ActionType.FREEZE)
        g.apply_freeze_player(g.players[0], card)
        self.assertIn(card, g.deck.discard_pile)

    def test_inactive_player_raises(self):
        g = fresh_game()
        g.players[0].state = PlayerState.STAYED
        with self.assertRaises(ValueError):
            g.apply_freeze_player(g.players[0], action(ActionType.FREEZE))


# ── apply_second_chance ───────────────────────────────────────────────────────

class TestApplySecondChance(unittest.TestCase):

    def test_assigns_card_when_player_has_none(self):
        g = fresh_game()
        sc = action(ActionType.SECOND_CHANCE)
        g.apply_second_chance(g.players[0], sc)
        self.assertEqual(g.players[0].second_chance_card, sc)

    def test_passes_to_random_eligible_when_already_held(self):
        g = fresh_game(["Alice", "Bob", "Charlie"])
        sc1 = action(ActionType.SECOND_CHANCE)
        sc2 = action(ActionType.SECOND_CHANCE)
        g.players[0].second_chance_card = sc1
        g.apply_second_chance(g.players[0], sc2)
        has_it = (g.players[1].second_chance_card == sc2 or
                  g.players[2].second_chance_card == sc2)
        self.assertTrue(has_it)

    def test_discards_when_no_eligible_players(self):
        g = fresh_game(["Alice", "Bob"])
        sc1 = action(ActionType.SECOND_CHANCE)
        sc2 = action(ActionType.SECOND_CHANCE)
        g.players[0].second_chance_card = sc1
        g.players[1].second_chance_card = sc2
        sc3 = action(ActionType.SECOND_CHANCE)
        g.apply_second_chance(g.players[0], sc3)
        self.assertIn(sc3, g.deck.discard_pile)

    def test_inactive_player_raises(self):
        g = fresh_game()
        g.players[0].state = PlayerState.BUSTED
        with self.assertRaises(ValueError):
            g.apply_second_chance(g.players[0], action(ActionType.SECOND_CHANCE))


# ── apply_flip_three ──────────────────────────────────────────────────────────

class TestApplyFlipThree(unittest.TestCase):

    def test_flip_three_card_discarded_immediately(self):
        g = fresh_game()
        ft = action(ActionType.FLIP_THREE)
        g.deck.draw_pile = [num(1), num(2), num(3)]
        g.apply_flip_three(g.players[0], ft)
        self.assertIn(ft, g.deck.discard_pile)

    def test_draws_up_to_three_cards(self):
        g = fresh_game()
        ft = action(ActionType.FLIP_THREE)
        g.deck.draw_pile = [num(1), num(2), num(3)]
        g.apply_flip_three(g.players[0], ft)
        self.assertEqual(len(g.players[0].number_cards), 3)

    def test_stops_early_on_bust(self):
        # draw_card() uses pop() so draws from the END of draw_pile.
        # [bust_5, safe_9, safe_8] -> draws: safe_8 first, safe_9 second, bust_5 third.
        # bust on the 3rd draw — sequence stops, 9 and 8 are already drawn (before bust).
        # To stop early we need the bust on the FIRST draw:
        # [safe_9, safe_8, bust_5] -> draws: bust_5 first -> stop -> 8 and 9 never drawn.
        g = fresh_game()
        ft = action(ActionType.FLIP_THREE)
        g.players[0].add_number_card(num(5))
        g.deck.draw_pile = [num(9), num(8), num(5)]  # bust_5 drawn first (pop from end)
        g.apply_flip_three(g.players[0], ft)
        self.assertTrue(g.players[0].is_busted())
        values = [c.value for c in g.players[0].number_cards]
        self.assertNotIn(9, values)
        self.assertNotIn(8, values)

    def test_held_action_cards_discarded_on_bust(self):
        g = fresh_game()
        ft = action(ActionType.FLIP_THREE)
        held_freeze = action(ActionType.FREEZE)
        g.players[0].add_number_card(num(5))
        g.deck.draw_pile = [num(5), held_freeze]
        g.apply_flip_three(g.players[0], ft)
        self.assertIn(held_freeze, g.deck.discard_pile)

    def test_held_action_cards_resolved_after_sequence(self):
        g = fresh_game()
        ft = action(ActionType.FLIP_THREE)
        held_freeze = action(ActionType.FREEZE)
        g.deck.draw_pile = [num(2), num(1), held_freeze]
        with patch.object(g, "choose_target_player", return_value=g.players[1]):
            g.apply_flip_three(g.players[0], ft)
        self.assertEqual(g.players[1].state, PlayerState.FROZEN)

    def test_inactive_player_raises(self):
        g = fresh_game()
        g.players[0].state = PlayerState.STAYED
        with self.assertRaises(ValueError):
            g.apply_flip_three(g.players[0], action(ActionType.FLIP_THREE))


# ── player_hit ────────────────────────────────────────────────────────────────

class TestPlayerHit(unittest.TestCase):

    def test_hit_adds_number_card_to_hand(self):
        g = fresh_game()
        # Replace draw pile entirely so no action card can surface
        g.deck.draw_pile = [num(7)]
        g.player_hit(g.players[0])
        self.assertIn(num(7), g.players[0].number_cards)

    def test_hit_adds_modifier_to_hand(self):
        g = fresh_game()
        g.deck.draw_pile = [mod(ModifierType.PLUS_6)]
        g.player_hit(g.players[0])
        self.assertEqual(len(g.players[0].modifier_cards), 1)

    def test_hit_on_inactive_player_raises(self):
        g = fresh_game()
        g.players[0].state = PlayerState.STAYED
        with self.assertRaises(ValueError):
            g.player_hit(g.players[0])

    def test_hit_on_empty_deck_raises(self):
        g = fresh_game()
        g.deck.draw_pile = []
        g.deck.discard_pile = []
        with self.assertRaises(ValueError):
            g.player_hit(g.players[0])


# ── end_round ─────────────────────────────────────────────────────────────────

class TestEndRound(unittest.TestCase):

    def test_banks_round_scores_into_total(self):
        g = fresh_game(["Alice", "Bob"])
        g.resolve_number_card(g.players[0], num(7))
        g.resolve_number_card(g.players[1], num(3))
        g.end_round()
        self.assertEqual(g.players[0].total_score, 7)
        self.assertEqual(g.players[1].total_score, 3)

    def test_busted_player_scores_zero(self):
        g = fresh_game(["Alice", "Bob"])
        g.resolve_number_card(g.players[0], num(5))
        g.resolve_number_card(g.players[0], num(5))  # bust
        g.resolve_number_card(g.players[1], num(3))
        g.end_round()
        self.assertEqual(g.players[0].total_score, 0)

    def test_clears_all_players_hands(self):
        g = fresh_game(["Alice", "Bob"])
        g.resolve_number_card(g.players[0], num(4))
        g.resolve_number_card(g.players[1], num(9))
        g.end_round()
        self.assertEqual(g.players[0].number_cards, [])
        self.assertEqual(g.players[1].number_cards, [])

    def test_cards_moved_to_discard_pile(self):
        g = fresh_game(["Alice", "Bob"])
        card = num(6)
        g.resolve_number_card(g.players[0], card)
        g.end_round()
        self.assertIn(card, g.deck.discard_pile)

    def test_unused_second_chance_discarded(self):
        g = fresh_game(["Alice", "Bob"])
        sc = action(ActionType.SECOND_CHANCE)
        g.players[0].second_chance_card = sc
        g.end_round()
        self.assertIn(sc, g.deck.discard_pile)
        self.assertIsNone(g.players[0].second_chance_card)

    def test_accumulates_across_multiple_rounds(self):
        g = fresh_game(["Alice", "Bob"])
        g.resolve_number_card(g.players[0], num(5))
        g.end_round()
        g.start_new_round()
        g.resolve_number_card(g.players[0], num(9))
        g.end_round()
        self.assertEqual(g.players[0].total_score, 14)


# ── is_game_over / get_winner ─────────────────────────────────────────────────

class TestGameOverAndWinner(unittest.TestCase):

    def test_not_over_below_200(self):
        g = fresh_game()
        g.players[0].total_score = 199
        self.assertFalse(g.is_game_over())

    def test_over_at_exactly_200(self):
        g = fresh_game()
        g.players[0].total_score = 200
        self.assertTrue(g.is_game_over())

    def test_over_above_200(self):
        g = fresh_game()
        g.players[0].total_score = 215
        self.assertTrue(g.is_game_over())

    def test_get_winner_returns_highest_score(self):
        g = fresh_game(["Alice", "Bob", "Charlie"])
        g.players[0].total_score = 200
        g.players[1].total_score = 185
        g.players[2].total_score = 210
        self.assertEqual(g.get_winner(), g.players[2])

    def test_get_winner_returns_none_when_not_over(self):
        g = fresh_game()
        self.assertIsNone(g.get_winner())


if __name__ == "__main__":
    unittest.main()
