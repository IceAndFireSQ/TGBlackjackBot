import random

def deal_card():
    cards = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    return random.choice(cards)

def calculate_hand_value(hand):
    value = 0
    aces = 0
    for card in hand:
        if card in ['K', 'Q', 'J']:
            value += 10
        elif card == 'A':
            aces += 1
            value += 11
        else:
            value += int(card)

    while value > 21 and aces:
        value -= 10
        aces -= 1

    return value

def check_winner(player_value, bot_value):
    if player_value > 21:
        return "Bot wins!"
    elif bot_value > 21:
        return "Player wins!"
    elif player_value == bot_value:
        return "It's a draw!"
    elif player_value > bot_value:
        return "Player wins!"
    else:
        return "Bot wins!"

def format_hand(hand):
    return ', '.join(hand)
