import random
from rules_engine import cards

class Deck:
    def __init__(self):
        self.draw_pile = cards.build_deck()
        self.discard_pile = []

    def shuffle(self):
        random.shuffle(self.draw_pile)
    
    def draw_card(self):
        if self.draw_pile:
            return self.draw_pile.pop()   
        elif self.discard_pile:
            self.draw_pile = self.discard_pile
            self.discard_pile = []
            self.shuffle()
            return self.draw_card()
        else:
            return None
        
    def discard_card(self, cards_to_discard: list[cards.Card]):
        self.discard_pile.extend(cards_to_discard)

    def cards_remaining(self):
        return len(self.draw_pile)