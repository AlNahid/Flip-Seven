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

    def player_stay(self, player: Player):
        if player.is_active() and player.has_number_cards():
            player.state = PlayerState.STAYED
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
            if player.busted():
                raise ValueError(f"Player {player.name} has busted with duplicate number cards.")
            elif player.has_flip_seven():
                self.flip_seven_triggered = True
        
        else:
            raise ValueError (f"Player {player.name} is not active.")
        
        return None
    
    # next time: implement the logic for resolving action cards