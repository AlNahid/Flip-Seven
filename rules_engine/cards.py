from dataclasses import dataclass
from enum import Enum

class CardType(Enum):
    NUMBER = 1
    MODIFIER = 2
    ACTION = 3

class ModifierType(Enum):
    PLUS_2 = 2
    PLUS_4 = 4
    PLUS_6 = 6
    PLUS_8 = 8
    PLUS_10 = 10
    TIMES_2 = 22

class ActionType(Enum):
    FREEZE = 1
    SECOND_CHANCE = 2
    FLIP_THREE = 3

@dataclass
class Card:
    category: CardType
    value: int | ModifierType | ActionType

def build_deck() -> list[Card]:
    deck = []
    # Add number cards
    for i in range(0, 13):
        if i == 0:
            deck.append(Card(CardType.NUMBER, 0))
        else:
            for _ in range(i):
                deck.append(Card(CardType.NUMBER, i))
    
    # Add modifier cards
    for modifier in ModifierType:
        deck.append(Card(CardType.MODIFIER, modifier))
    
    # Add action cards
    for action in ActionType:
        for _ in range(3):  # Add two of each action card
            deck.append(Card(CardType.ACTION, action))
    
    return deck
