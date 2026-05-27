from app.game.deck import Card, Deck


def test_standard_deck_has_52_unique_cards():
    deck = Deck()

    assert len(deck.cards) == 52
    assert len(set(deck.cards)) == 52


def test_deal_removes_cards_from_the_top_of_the_deck():
    deck = Deck(cards=[Card.from_str("As"), Card.from_str("Kd"), Card.from_str("Qc")])

    dealt = deck.deal(2)

    assert dealt == [Card.from_str("As"), Card.from_str("Kd")]
    assert deck.cards == [Card.from_str("Qc")]
