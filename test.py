from rules_engine.cards import Card, CardType
from rules_engine.player import Player

p = Player("Alice")
p.add_number_card(Card(CardType.NUMBER, 7))
p.add_number_card(Card(CardType.NUMBER, 3))

print(p.has_number(7))   # should be True
print(p.has_number(3))   # should be True
print(p.has_number(9))   # should be False
print(p.has_number(0))   # should be False