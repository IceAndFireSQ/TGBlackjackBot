from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from db_utils import get_balance, update_balance, create_tables
from game_utils import deal_card, calculate_hand_value, check_winner, format_hand

games = {}


def get_game_buttons(user_id):
    buttons = []

    # Check if the player has split
    if len(games[user_id]['player_hands']) > 1:
        # Show actions for each hand after a split
        for i in range(len(games[user_id]['player_hands'])):
            buttons.append([InlineKeyboardButton(f"Hit {i + 1}", callback_data=f"hit{i + 1}")])
            buttons.append([InlineKeyboardButton(f"Stand {i + 1}", callback_data=f"stand{i + 1}")])
    else:
        # Show initial actions for the first hand
        if not games[user_id].get("first_action", False):
            buttons.append([InlineKeyboardButton("Hit", callback_data="hit")])
            buttons.append([InlineKeyboardButton("Stand", callback_data="stand")])
            buttons.append([InlineKeyboardButton("Double", callback_data="double")])
            buttons.append([InlineKeyboardButton("Split", callback_data="split")])
        else:
            # If the first action has been taken, show only hit/stand for the first hand
            buttons.append([InlineKeyboardButton("Hit", callback_data="hit")])
            buttons.append([InlineKeyboardButton("Stand", callback_data="stand")])

    buttons.append([InlineKeyboardButton("Main Menu", callback_data="menu")])
    return InlineKeyboardMarkup(buttons)


def get_end_game_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Play Again", callback_data="play")],
        [InlineKeyboardButton("Check Balance", callback_data="balance")],
        [InlineKeyboardButton("Main Menu", callback_data="menu")]
    ])


def get_main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Check Balance", callback_data="balance")],
        [InlineKeyboardButton("Play Blackjack", callback_data="play")],
        [InlineKeyboardButton("Info", callback_data="info")]
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    create_tables()
    await update.message.reply_text(
        "Welcome to Blackjack!",
        reply_markup=get_main_menu()
    )
    update_balance(user_id, 100)


async def handle_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.message.chat_id
    await query.answer()
    action = query.data
    if action == "menu":
        await query.edit_message_text("Main Menu", reply_markup=get_main_menu())
    elif action == "balance":
        await balance(query, context)
    elif action == "play":
        await play(query, context)
    elif action.startswith("hit"):
        await hit(query, context, action)
    elif action.startswith("stand"):
        await stand(query, context, action)
    elif action == "double":
        await double(query, context)
    elif action == "split":
        await split(query, context)
    elif action == "info":
        await info(query, context)


async def balance(query: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = query.message.chat_id
    await query.message.reply_text(f"Your balance is: ${get_balance(user_id):.2f}")


async def play(query: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = query.message.chat_id
    if user_id in games:
        await query.message.reply_text("Finish your current game first.")
        return
    if get_balance(user_id) < 10:
        await query.message.reply_text("You don't have enough credits to play.")
        return
    player_hand = [deal_card(), deal_card()]
    bot_hand = [deal_card(), deal_card()]
    games[user_id] = {
        'player_hands': [player_hand],
        'bot_hand': bot_hand,
        'player_values': [calculate_hand_value(player_hand)],
        'bot_value': calculate_hand_value(bot_hand),
        'bet': 10,
        'first_action': False,
        'active_hand': 0
    }
    update_balance(user_id, -10)
    await query.message.reply_text(
        f"Your hands: {format_hand(player_hand)}\nBot's hand: {bot_hand[0]}, ?",
        reply_markup=get_game_buttons(user_id)
    )


async def hit(query: Update, context: ContextTypes.DEFAULT_TYPE, action: str):
    user_id = query.message.chat_id
    if user_id not in games:
        await query.message.reply_text("Start a new game first.")
        return

    # Determine which hand to hit
    if action.startswith("hit"):
        if action == "hit":
            hand_index = 0  # First hand
        else:
            hand_index = int(action[-1]) - 1  # Get hand index from action

        card = deal_card()
        games[user_id]['player_hands'][hand_index].append(card)
        games[user_id]['player_values'][hand_index] = calculate_hand_value(games[user_id]['player_hands'][hand_index])

        if games[user_id]['player_values'][hand_index] > 21:
            await query.message.reply_text(
                f"You hit: {card}. Your hand: {format_hand(games[user_id]['player_hands'][hand_index])}. You busted! Bot wins!",
                reply_markup=get_end_game_buttons()
            )
            del games[user_id]  # Remove the game for this user
            return

        # Update the message to reflect the correct hand display
        hand_message = f"Your hand: {format_hand(games[user_id]['player_hands'][hand_index])}"
        await query.message.reply_text(
            f"You hit: {card}. {hand_message}",
            reply_markup=get_game_buttons(user_id)  # Update buttons after the action
        )

async def stand(query: Update, context: ContextTypes.DEFAULT_TYPE, action: str):
    user_id = query.message.chat_id
    if user_id not in games:
        await query.message.reply_text("Start a new game first.")
        return

    # Determine which hand to stand
    if action.startswith("stand"):
        if action == "stand":
            hand_index = 0  # First hand
        else:
            hand_index = int(action[-1]) - 1  # Get hand index from action

        # Mark the hand as stood
        await query.message.reply_text(
            f"You stand: {format_hand(games[user_id]['player_hands'][hand_index])}",
        )

        # Check if all hands have been stood
        if hand_index == len(games[user_id]['player_hands']) - 1:
            await resolve_game(query, user_id)  # Resolve the game if all hands are stood
        else:
            await query.message.reply_text("Now it's time for Hand 2.")


async def resolve_game(query: Update, user_id: str):
    bot_hand = games[user_id]['bot_hand']
    while games[user_id]['bot_value'] < 17:
        bot_hand.append(deal_card())
        games[user_id]['bot_value'] = calculate_hand_value(bot_hand)

    result = check_winner(games[user_id]['player_values'][0], games[user_id]['bot_value'])
    if result == "Player wins!":
        update_balance(user_id, 20)
    elif result == "It's a draw!":
        update_balance(user_id, 10)

    await query.message.reply_text(
        f"Bot's hand: {format_hand(bot_hand)} (Value: {games[user_id]['bot_value']})\nResult: {result}",
        reply_markup=get_end_game_buttons()
    )
    del games[user_id]

async def double(query: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = query.message.chat_id
    if user_id not in games:
        await query.message.reply_text("Start a new game first.")
        return

    # Ensure the player hasn't already taken an action
    if games[user_id]['first_action']:
        await query.message.reply_text("You can't double after taking an action.")
        return

    current_bet = games[user_id]['bet']
    if get_balance(user_id) < current_bet:
        await query.message.reply_text("Insufficient balance to double.")
        return

    # Double the bet and deal one more card
    update_balance(user_id, -current_bet)
    games[user_id]['bet'] = current_bet * 2
    card = deal_card()
    games[user_id]['player_hands'][0].append(card)
    games[user_id]['player_values'][0] = calculate_hand_value(games[user_id]['player_hands'][0])
    games[user_id]['first_action'] = True

    await query.message.reply_text(
        f"You doubled down and hit: {card}. Your hand: {format_hand(games[user_id]['player_hands'][0])}",
    )
    await resolve_game(query, user_id)  # Resolve the game after doubling down

async def split(query: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = query.message.chat_id
    if user_id not in games:
        await query.message.reply_text("Start a new game first.")
        return

    player_hand = games[user_id]['player_hands'][0]
    if len(player_hand) != 2 or player_hand[0] != player_hand[1]:
        await query.message.reply_text("You can only split with two identical cards.")
        return

    if get_balance(user_id) < games[user_id]['bet']:
        await query.message.reply_text("Insufficient balance to split.")
        return

    # Split the hand
    split_card = player_hand.pop()  # Remove one card from the original hand
    split_hand = [split_card]  # Start the second hand with the split card
    games[user_id]['player_hands'].append(split_hand)  # Add the new hand to the player's hands
    games[user_id]['player_values'].append(calculate_hand_value(split_hand))  # Calculate the value of the new hand
    update_balance(user_id, -games[user_id]['bet'])  # Deduct the bet for the split
    games[user_id]['first_action'] = False  # Reset first action for the new hands

    await query.message.reply_text(
        f"You split your hand.\nFirst hand: {format_hand(games[user_id]['player_hands'][0])}\n"
        f"Second hand: {format_hand(split_hand)}",
        reply_markup=get_game_buttons(user_id)  # Show buttons for the next actions
    )

async def info(query: Update, context: ContextTypes.DEFAULT_TYPE):
    info_text = (
        "Welcome to the Blackjack bot!\n"
        "Use the buttons to play:\n"
        "- Hit: Take another card for your active hand.\n"
        "- Stand: End your turn for your active hand.\n"
        "- Double: You can only double on your first move.\n"
        "- Split: You can only split on your first move with two identical cards.\n"
        "Enjoy the game!"
    )
    await query.message.reply_text(info_text, reply_markup=get_main_menu())
