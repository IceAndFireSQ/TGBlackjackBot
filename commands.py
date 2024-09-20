from telegram import Update
from telegram.ext import ContextTypes
from db_utils import get_balance, update_balance, create_tables
from game_utils import deal_card, calculate_hand_value, check_winner, format_hand

games = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    create_tables()
    await update.message.reply_text("Welcome to Blackjack! Use /menu to see commands.")
    update_balance(user_id, 100)  #Balance for new guys


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    commands = (
        "/balance - Check your balance\n"
        "/play - Start a new game\n"
        "/hit - Take another card\n"
        "/stand - End your turn\n"
        "/double - Double your bet\n"
        "/split - Split your hand"
    )
    await update.message.reply_text(commands)


async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    balance = get_balance(user_id)
    await update.message.reply_text(f"Your balance is: ${balance:.2f}")


async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    if user_id in games:
        await update.message.reply_text("You are already playing a game. Use /stand to finish your current game.")
        return

    if get_balance(user_id) < 10:
        await update.message.reply_text("You dont have enough credits to play.")
        return

    player_hand = [deal_card(), deal_card()]
    bot_hand = [deal_card(), deal_card()]

    games[user_id] = {
        'player_hand': player_hand,
        'bot_hand': bot_hand,
        'player_value': calculate_hand_value(player_hand),
        'bot_value': calculate_hand_value(bot_hand),
        'bet': 10
    }
    update_balance(user_id, -10)

    await update.message.reply_text(
        f"Your hand: {format_hand(player_hand)}\n"
        f"Bot's hand: {bot_hand[0]}, ?\n"
    )


async def hit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    if user_id not in games:
        await update.message.reply_text("You need to start a game first! Use /play.")
        return

    card = deal_card()
    games[user_id]['player_hand'].append(card)
    games[user_id]['player_value'] = calculate_hand_value(games[user_id]['player_hand'])

    if games[user_id]['player_value'] > 21:
        await update.message.reply_text(f"You hit: {card}. You bust! Game over.")
        del games[user_id]
    else:
        await update.message.reply_text(f"You hit: {card}. Your hand: {format_hand(games[user_id]['player_hand'])}")


async def stand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    if user_id not in games:
        await update.message.reply_text("You need to start a game first! Use /play.")
        return

    player_value = games[user_id]['player_value']
    bot_hand = games[user_id]['bot_hand']

    while games[user_id]['bot_value'] < 17:
        bot_hand.append(deal_card())
        games[user_id]['bot_value'] = calculate_hand_value(bot_hand)

    result = check_winner(player_value, games[user_id]['bot_value'])
    if result == "Player wins!":
        update_balance(user_id, 20)
    elif result == "It's a draw!":
        update_balance(user_id, 10)

    await update.message.reply_text(f"Your hand: {format_hand(games[user_id]['player_hand'])} (Value: {player_value})\n"
                                    f"Bot's hand: {format_hand(bot_hand)} (Value: {games[user_id]['bot_value']})\n"
                                    f"Result: {result}")
    del games[user_id]


async def double(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    if user_id not in games:
        await update.message.reply_text("You need to start a game first! Use /play.")
        return

    current_bet = games[user_id]['bet']
    new_bet = current_bet * 2
    update_balance(user_id, -current_bet)
    games[user_id]['bet'] = new_bet
    card = deal_card()
    games[user_id]['player_hand'].append(card)
    games[user_id]['player_value'] = calculate_hand_value(games[user_id]['player_hand'])

    player_value = games[user_id]['player_value']
    bot_hand = games[user_id]['bot_hand']
    while games[user_id]['bot_value'] < 17 and games[user_id]['player_value'] <= 21:
        bot_hand.append(deal_card())
        games[user_id]['bot_value'] = calculate_hand_value(bot_hand)
    result = check_winner(player_value, games[user_id]['bot_value'])
    if result == "Player wins!":
        update_balance(user_id, 40)
    elif result == "It's a draw!":
        update_balance(user_id, 20)

    await update.message.reply_text(f"Your hand: {format_hand(games[user_id]['player_hand'])} (Value: {player_value})\n"
                                    f"Bot's hand: {format_hand(bot_hand)} (Value: {games[user_id]['bot_value']})\n"
                                    f"Result: {result}")
    del games[user_id]


async def split(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    if user_id not in games:
        await update.message.reply_text("You need to start a game first! Use /play.")
        return

    player_hand = games[user_id]['player_hand']
    if len(player_hand) != 2 or player_hand[0] != player_hand[1]:
        await update.message.reply_text("You can only split when you have two identical cards.")
        return

    if get_balance(user_id) < games[user_id]['bet']:
        await update.message.reply_text("You don't have enough balance to split.")
        return

    split_card = player_hand.pop()
    split_hand = [split_card, deal_card()]
    games[user_id]['split_hand'] = split_hand
    games[user_id]['player_hand'].append(deal_card())

    games[user_id]['player_value'] = calculate_hand_value(games[user_id]['player_hand'])
    update_balance(user_id, -games[user_id]['bet'])

    await update.message.reply_text(
        f"You split your hand.\n"
        f"First hand: {format_hand(games[user_id]['player_hand'])}\n"
        f"Second hand: {format_hand(split_hand)}"
    )
