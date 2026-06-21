from dataclasses import dataclass
from enum import Enum
from rules_engine.cards import Card, CardType, ModifierType, ActionType

class PlayerState(Enum):
    ACTIVE = 1
    STAYED = 2
    BUSTED = 3
    FROZEN = 4
    FLIPPED = 5

class Player:
    def __init__(self, name: str):
        self.name = name
        self.total_score = 0
        self.round_score = 0
        self.number_cards: list[Card] = []
        self.modifier_cards: list[Card] = []
        self.second_chance_card : Card | None = None
        self.state: PlayerState = PlayerState.ACTIVE

    def is_active(self) -> bool:
        return self.state == PlayerState.ACTIVE
    
    def is_flipped(self) -> bool:
        return self.state == PlayerState.FLIPPED

    def is_busted(self) -> bool:
        return self.state == PlayerState.BUSTED

    def has_number_cards(self) -> bool:
        return len(self.number_cards) > 0
    
    def has_modifier_cards(self) -> bool:
        return len(self.modifier_cards) > 0
    
    def has_flip_seven(self) -> bool:
        if len(self.number_cards) == 7:
            self.state = PlayerState.FLIPPED
            return True
        return False

    def busted(self):
        values = [card.value for card in self.number_cards]
        if len(values) != len(set(values)):
            self.state = PlayerState.BUSTED
            return True
        return False

    def add_number_card(self, card: Card):
        if card.category == CardType.NUMBER:
            self.number_cards.append(card)
        else:
            raise ValueError("Card must be a number card.")
    def add_modifier_card(self, card: Card):
        if card.category == CardType.MODIFIER:
            self.modifier_cards.append(card)
        else:
            raise ValueError("Card must be a modifier card.")
        
    def get_round_score(self) -> int:
        score = 0
        if self.is_busted():
            score = 0
        else:
            for card in self.number_cards:
                score += card.value

            for card in self.modifier_cards:
                if card.value == ModifierType.TIMES_2:
                    score *= 2

            for card in self.modifier_cards:
                if card.value == ModifierType.PLUS_2:
                    score += 2
                elif card.value == ModifierType.PLUS_4:
                    score += 4
                elif card.value == ModifierType.PLUS_6:
                    score += 6
                elif card.value == ModifierType.PLUS_8:
                    score += 8
                elif card.value == ModifierType.PLUS_10:
                    score += 10
                elif card.value == ModifierType.TIMES_2:
                    continue

            if self.has_flip_seven():
                score += 15

        self.round_score = score
        return self.round_score

    def get_total_score(self) -> int:
        self.total_score += self.round_score
        return self.total_score

    def reset_round(self):
        self.round_score = 0
        self.number_cards.clear()
        self.modifier_cards.clear()
        self.second_chance_card = None
        self.state = PlayerState.ACTIVE
