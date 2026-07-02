import random
from rules_engine import deck
from rules_engine.player import Player, PlayerState
from rules_engine.cards import Card, CardType, ModifierType, ActionType

class Game:
    def __init__(self, players: list[str]):
        self.players = [Player(name) for name in players]
        self.deck = deck.Deck()
        self.first_player_index = 0
        self.current_player_index = (self.first_player_index + 1) % len(self.players)
        self.round_number = 0
        self.flip_seven_triggered = False
        self.log = []
    

    def active_players(self) -> list[Player]:
        return [player for player in self.players if player.is_active()]
    
    def is_round_over(self) -> bool:
        if self.flip_seven_triggered or len(self.active_players()) == 0:
            return True
        return False

    def start_new_round(self):
        self.round_number += 1
        self.flip_seven_triggered = False
        for player in self.players:
            player.reset_round()
        self.first_player_index = (self.first_player_index + 1) % len(self.players)
        self.current_player_index = (self.first_player_index + 1) % len(self.players)
        self.deck.shuffle()
        self.log.append(f"--- Round {self.round_number} started ---")

    def player_stay(self, player: Player):
        if player.is_active() and player.has_number_cards():
            player.state = PlayerState.STAYED
            self.log.append(f"{player.name} chose to Stay")
        else:
            raise ValueError("Player cannot stay without any number cards.")
        
    def next_active_player(self):
        if not self.is_round_over():
            current_index = self.current_player_index
            found = False
            count = 0
            while count < len(self.players):
                current_index = (current_index + 1) % len(self.players)
                if self.players[current_index].is_active():
                    self.current_player_index = current_index
                    found = True
                    break
                count += 1
            if found:
                return self.players[self.current_player_index]
            else:
                raise ValueError("No active players left.")
        else:
            raise ValueError("No active players left.")

    def resolve_number_card(self, player: Player, card: Card):
        if player.is_active():
            player.add_number_card(card)
            self.log.append(f"{player.name} drew number card {card.value}")
            if player.busted():
                if player.second_chance_card is not None:
                    player.number_cards.remove(card)
                    self.deck.discard_card([card, player.second_chance_card])
                    player.second_chance_card = None
                    player.state = PlayerState.ACTIVE
                    self.log.append(f"{player.name} was saved by Second Chance!")
                else:
                    self.log.append(f"{player.name} busted!")    
                    return
            if not player.is_busted() and player.has_flip_seven():
                self.flip_seven_triggered = True
                self.log.append(f"{player.name} hit Flip 7!")    
        else:
            raise ValueError (f"Player {player.name} is not active.")
    
    def resolve_modifier_card(self, player: Player, card: Card):
        if player.is_active():
            player.add_modifier_card(card)
            self.log.append(f"{player.name} drew modifier {card.value.name}")
        else:
            raise ValueError (f"Player {player.name} is not active.")
        
    def apply_freeze_player(self, player: Player, card: Card):
        if player.is_active():
            self.deck.discard_card([card])
            player.state = PlayerState.FROZEN
            self.log.append(f"{player.name} was frozen!")
        else:
            raise ValueError(f"Player {player.name} is not active.")
        
    def apply_second_chance(self, receiving_player: Player, card: Card):
        if receiving_player.is_active():
            receiving_player.second_chance_card = card
            self.log.append(f"{receiving_player.name} received a Second Chance card")
        else:
            raise ValueError(f"Player {receiving_player.name} is not active.")
        
    def apply_flip_three(self, player: Player, card: Card):
        self.log.append(f"{player.name} must draw 3 cards (Flip Three)!")
        self.deck.discard_card([card])
        cards_on_hold = []
        if player.is_active():
            for i in range(3):
                card = self.deck.draw_card()
                if card is None: break
                if card.category == CardType.NUMBER:
                    self.resolve_number_card(player, card)
                    if player.is_busted() or self.flip_seven_triggered:
                        break
                elif card.category == CardType.MODIFIER:
                    self.resolve_modifier_card(player, card)
                elif card.category == CardType.ACTION:
                    cards_on_hold.append(card)
            if player.is_busted() or self.flip_seven_triggered:
                if cards_on_hold:
                    self.deck.discard_card(cards_on_hold)
            else:
                for held_card in cards_on_hold:
                    self.resolve_action_card(player, held_card)
        else:
            raise ValueError(f"Player {player.name} is not active.")
        
    def resolve_action_card(self, receiving_player: Player, card: Card):
        target_player = self.choose_target_player(receiving_player, card)
        if target_player is None:
            return
        if card.value == ActionType.FREEZE:
            self.apply_freeze_player(target_player, card)
        elif card.value == ActionType.SECOND_CHANCE:
            self.apply_second_chance(target_player, card)
        elif card.value == ActionType.FLIP_THREE:
            self.apply_flip_three(target_player, card)
        else:
            raise ValueError(f"Unknown action type: {card.value}")
    
    def choose_target_player(self, receiving_player: Player, card: Card) -> Player:
        if card.value == ActionType.SECOND_CHANCE:
            eligible_players = [p for p in self.active_players() 
                                if p.second_chance_card is None]
        else:
            eligible_players = self.active_players()
        print(f"Eligible players for targeting:")
        for i in range(len(eligible_players)):
            print(f"{i + 1}. {eligible_players[i].name}")
        print(f"{receiving_player.name}, choose a player to target:")
        while True:
            try:
                choice = int(input())
                if 1 <= choice <= len(eligible_players):
                    return eligible_players[choice - 1]
                else:
                    print("Invalid choice. Please try again.")
            except ValueError:
                print("Invalid input. Please enter a number.")

    def deal_initial_cards(self):
        for i in range (len(self.players)):
            if self.is_round_over():
                break
            index = (self.first_player_index + i) % len(self.players)
            player = self.players[index]
            card = self.deck.draw_card()
            if card is None:
                raise ValueError("Deck is empty. Cannot deal initial cards.")
            if card.category == CardType.NUMBER:
                self.resolve_number_card(player, card)
            elif card.category == CardType.MODIFIER:
                self.resolve_modifier_card(player, card)
            elif card.category == CardType.ACTION:
                self.resolve_action_card(player, card)

    def player_hit(self, player: Player):
        if player.is_active():
            card = self.deck.draw_card()
            if card is None:
                raise ValueError("Deck is empty. Cannot draw a card.")
            if card.category == CardType.NUMBER:
                self.resolve_number_card(player, card)
            elif card.category == CardType.MODIFIER:
                self.resolve_modifier_card(player, card)
            elif card.category == CardType.ACTION:
                self.resolve_action_card(player, card)
        else:
            raise ValueError(f"Player {player.name} is not active.")
    
    def end_round(self):
        self.log.append(f"--- Round {self.round_number} ended ---")
        for player in self.players:
            player.get_round_score()
            player.get_total_score()
            collect_cards = player.number_cards + player.modifier_cards
            if player.second_chance_card is not None:
                collect_cards.append(player.second_chance_card)
            self.deck.discard_card(collect_cards)
            player.reset_round()

    def is_game_over(self) -> bool:
        return any(player.total_score >= 200 for player in self.players)
    
    def get_winner(self) -> Player | None:
        if self.is_game_over():
            return max(self.players, key=lambda p: p.total_score)
        return None


