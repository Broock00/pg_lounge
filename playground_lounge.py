import logging
import asyncio
from typing import Final
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import uuid
import os
# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN: Final = os.getenv("BOT_TOKEN")

# MENU
MENU = {
    "Drinks": [
        {"name": "Sprite", "price": 10, "description": "A refreshing minty cocktail."},
        {"name": "Beer (Draft)", "price": 6, "description": "Chilled and crisp."},
        {"name": "Cola", "price": 3, "description": "Classic soda."},
    ],
    "Foods": [
        {"name": "Nachos", "price": 8, "description": "With cheese and salsa."},
        {"name": "Chicken Wings", "price": 12, "description": "Spicy or BBQ glazed wings."},
        {"name": "Cheeseburger", "price": 15, "description": "Juicy beef patty with cheese."},
        {"name": "Pizza", "price": 14, "description": "Classic with fresh basil."},
        {"name": "Fries", "price": 5, "description": "Crispy golden fries."},
    ]
}

# Store user orders, seen users, and pending orders
user_orders = {}
seen_users = set()
pending_orders = {}

# Staff group chat ID
STAFF_GROUP_CHAT_ID = os.getenv("GROUP_ID")

# Start command - Welcome message
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user.first_name
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    logger.info(f"Start command used by User ID: {user_id} in chat ID: {chat_id}")
    if user_id not in seen_users:
        seen_users.add(user_id)
        logger.info(f"New user detected: {user} (ID: {user_id})")
    await update.message.reply_text(
        f"Welcome to Playground Lounge, {user}! 🎉\n"
        "Use /menu to see what’s on offer or /help for more options."
    )

# Help command - List available commands
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    logger.info(f"Help command used in chat ID: {chat_id}")
    await update.message.reply_text(
        "Here’s what I can do:\n"
        "/menu - View the menu\n"
        "/order - Check or confirm your order\n"
        "/comment - Leave feedback\n"
        "/help - Show this message"
    )

# Menu command
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    logger.info(f"Menu command used in chat ID: {chat_id}")
    keyboard = [
        [InlineKeyboardButton("Drinks", callback_data="menu_drinks")],
        [InlineKeyboardButton("Foods", callback_data="menu_foods")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🍽️ What would you like to see?", reply_markup=reply_markup)

# Comment command
async def comment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    logger.info(f"Comment command used in chat ID: {chat_id}")
    context.user_data["awaiting_comment"] = True
    await update.message.reply_text("How was the service? Please type your feedback below.")

# Handle text input (e.g., quantities, comments, or cancel reason)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text.strip()
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    chat_type = update.message.chat.type

    if chat_type in ["group", "supergroup"]:
        logger.info(f"Message in group chat - Chat ID: {chat_id}")

    # Handle comment input
    if context.user_data.get("awaiting_comment", False):
        context.user_data["awaiting_comment"] = False
        feedback_message = f"💬 Feedback from User ID {user_id}:\n{text}"
        await context.bot.send_message(chat_id=STAFF_GROUP_CHAT_ID, text=feedback_message)
        await update.message.reply_text("Thanks for your feedback! We’ll pass it along to the team. 😊")
        logger.info(f"Comment from {user_id} in chat {chat_id}: {text}")
        return

    # Handle quantity input
    if context.user_data.get("awaiting_quantity", False):
        item_key = context.user_data["awaiting_quantity"]
        category = context.user_data["last_category"]
        selected_items = context.user_data.get("selected_items", {})
        
        if text.isdigit() and int(text) > 0:
            quantity = int(text)
        else:
            quantity = 1
            await update.message.reply_text("Invalid number, defaulting to 1.")

        selected_items[item_key] = quantity
        context.user_data["awaiting_quantity"] = False
        reply_markup = await build_menu_keyboard(category, context.user_data)
        await update.message.reply_text(f"Set quantity to {quantity} for {MENU[category][int(item_key.split('_')[1])]['name']}.", reply_markup=reply_markup)
        return

    # Handle cancel reason input from staff
    if chat_id == STAFF_GROUP_CHAT_ID and context.user_data.get("awaiting_cancel_reason", False):
        order_id = context.user_data["awaiting_cancel_reason"]
        if order_id in pending_orders:
            reason = text or "No reason provided."
            pending_orders[order_id]["status"] = "canceled"
            user_chat_id = pending_orders[order_id]["chat_id"]
            await context.bot.send_message(
                chat_id=user_chat_id,
                text=f"Try Again, Your order (ID: {order_id}) was canceled. Reason: {reason}"
            )
            await update.message.reply_text(f"Order ID: {order_id} canceled. Reason sent to user: {reason}")
            del pending_orders[order_id]
            context.user_data["awaiting_cancel_reason"] = False
        return

# Order command
async def order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    logger.info(f"Order command used in chat ID: {chat_id}")
    if user_id not in user_orders or not user_orders[user_id]:
        await update.message.reply_text("You haven’t ordered anything yet! Use /menu to start.")
        return

    total = 0
    response = "🛒 Your Order:\n"
    for item in user_orders[user_id]:
        qty = item.get("quantity", 1)
        response += f"- {item['name']} x{qty} (ETB {item['price'] * qty})\n"
        total += item["price"] * qty
    response += f"\nTotal: ETB {total}"

    keyboard = [
        [InlineKeyboardButton("Confirm Order", callback_data="order_confirm")],
        [InlineKeyboardButton("Cancel Order", callback_data="order_clear")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(response, reply_markup=reply_markup)

# Build menu keyboard with checkboxes
async def build_menu_keyboard(category: str, user_data: dict) -> InlineKeyboardMarkup:
    items = MENU.get(category, [])
    keyboard = []
    selected_items = user_data.get("selected_items", {})

    for idx, item in enumerate(items):
        item_key = f"{category}_{idx}"
        quantity = selected_items.get(item_key, 0)
        button_text = f"✓ {item['name']} x{quantity} (ETB {item['price']})" if quantity else f"{item['name']} (ETB {item['price']})"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"toggle_{item_key}")])

    keyboard.append([InlineKeyboardButton("Done", callback_data=f"done_{category}")])
    return InlineKeyboardMarkup(keyboard)

# Retry sending message with exponential backoff
async def send_message_with_retry(bot, chat_id, text, reply_markup=None, max_retries=3):
    for attempt in range(max_retries):
        try:
            await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)
            logger.info(f"Message sent successfully to chat ID: {chat_id}")
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"All {max_retries} attempts failed: {str(e)}")
                return False

# Handle button clicks (menu and order actions)
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    user_id = query.from_user.id

    if "selected_items" not in context.user_data:
        context.user_data["selected_items"] = {}

    if query.data.startswith("menu_"):
        category = query.data.split("_")[1].capitalize()
        context.user_data["last_category"] = category
        reply_markup = await build_menu_keyboard(category, context.user_data)
        await query.edit_message_text(f"🍴 {category} Menu 🍴\n\nSelect items:", reply_markup=reply_markup)

    elif query.data.startswith("toggle_"):
        item_key = query.data.split("_")[1] + "_" + query.data.split("_")[2]
        category = context.user_data["last_category"]
        context.user_data["awaiting_quantity"] = item_key
        item_idx = int(item_key.split("_")[1])
        item_name = MENU[category][item_idx]["name"]
        await query.edit_message_text(f"How many {item_name}s would you like? Enter a number (default is 1):")

    elif query.data.startswith("done_"):
        category = query.data.split("_")[1].capitalize()
        selected_items = context.user_data["selected_items"]
        if user_id not in user_orders:
            user_orders[user_id] = []

        for item_key, quantity in selected_items.items():
            if quantity > 0 and item_key.startswith(category):
                idx = int(item_key.split("_")[1])
                item = MENU[category][idx].copy()
                item["quantity"] = quantity
                user_orders[user_id].append(item)

        context.user_data["selected_items"] = {}
        await query.edit_message_text(
            f"Items from {category} added to your order!\nUse /order to view or confirm."
        )

    elif query.data == "order_confirm":
        logger.info(f"Order confirmed in chat ID: {chat_id}")
        if user_id in user_orders and user_orders[user_id]:
            user_name = query.from_user.first_name
            if query.from_user.last_name:
                user_name += f" {query.from_user.last_name}"

            order_id = str(uuid.uuid4())[:8]
            total = 0
            order_summary = f"🔔 New Order from {user_name} (User ID: {user_id}):\nOrder ID: {order_id}\n"
            for item in user_orders[user_id]:
                qty = item.get("quantity", 1)
                order_summary += f"- {item['name']} x{qty} (ETB {item['price'] * qty})\n"
                total += item["price"] * qty
            order_summary += f"\nTotal: ETB {total}"

            # Add buttons for staff
            keyboard = [
                [InlineKeyboardButton("Complete", callback_data=f"complete_{order_id}")],
                [InlineKeyboardButton("Cancel", callback_data=f"cancel_{order_id}")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Store order in pending_orders
            pending_orders[order_id] = {
                "user_id": user_id,
                "chat_id": chat_id,
                "items": user_orders[user_id].copy(),
                "total": total,
                "status": "pending"
            }

            # Prepare confirmation message for user
            confirmation_message = "✅ Order confirmed!\nYour orders:-\n"
            for item in user_orders[user_id]:
                qty = item.get("quantity", 1)
                confirmation_message += f"     ✓ {item['name']} x{qty} - ETB {item['price'] * qty}\n"
            confirmation_message += "Your items are being prepared. Enjoy your time at Playground Lounge! 🍹"

            # Send to staff with retry
            success = await send_message_with_retry(context.bot, STAFF_GROUP_CHAT_ID, order_summary, reply_markup)
            if success:
                await query.edit_message_text(confirmation_message)
                user_orders[user_id] = []
            else:
                await query.edit_message_text("Order prepared, but we couldn’t notify staff. Please inform them manually.")
        else:
            await query.edit_message_text("No order to confirm! Use /menu to start ordering.")

    elif query.data == "order_clear":
        # logger.info(f"Order canceled in chat ID: {chat_id}")
        user_orders[user_id] = []
        await query.edit_message_text("🗑️ Order canceled! Start fresh with /menu.")

    # Handle staff complete action
    elif query.data.startswith("complete_"):
        order_id = query.data.split("_")[1]
        if order_id in pending_orders and chat_id == STAFF_GROUP_CHAT_ID:
            pending_orders[order_id]["status"] = "completed"
            await query.edit_message_text(f"{query.message.text}\n\n✅ Order ID: {order_id} marked as completed.")
            del pending_orders[order_id]

    # Handle staff cancel action
    elif query.data.startswith("cancel_"):
        order_id = query.data.split("_")[1]
        if order_id in pending_orders and chat_id == STAFF_GROUP_CHAT_ID:
            context.user_data["awaiting_cancel_reason"] = order_id
            await query.edit_message_text(f"{query.message.text}\n\nPlease enter the reason for canceling Order ID: {order_id}:")

# Main function to run the bot
def main() -> None:
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(CommandHandler("order", order))
    application.add_handler(CommandHandler("comment", comment))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button))

    application.run_polling()

if __name__ == '__main__':
    main()
