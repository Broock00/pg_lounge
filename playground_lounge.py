import os
import logging
from typing import Final
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler,
)
 
# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token and staff group
TOKEN: Final = os.getenv("BOT_TOKEN")
STAFF_GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID", "0"))

# Menu data
MENU = {
    "Drinks": {
        "items": [
            {"name": "Blue Label", "price": 60000, "description": "Premium whisky 💎", "image_file_id": "AgACAgQAAxkBAANUZ_EmOD0zUD2R4o78cgoCsMTXhsEAAlTEMRtPHohT3k2T0b96lRABAAMCAAN4AAM2BA"},
            {"name": "Gold Label", "price": 20000, "description": "Luxury in a bottle ✨", "image_file_id": "AgACAgQAAxkBAANcZ_EmyV6qboXNAu3UP4vlrFk97H4AAljEMRtPHohTBNFbR-PhVXEBAAMCAAN5AAM2BA"},
            {"name": "Dabl Black", "price": 15000, "description": "Dark & bold 🖤", "image_file_id": "AgACAgQAAxkBAANaZ_EmpFvPp8LLsW8YI8N3amfMmzIAAlfEMRtPHohToO3o1ZctnhoBAAMCAAN5AAM2BA"},
            {"name": "Black Label", "price": 12000, "description": "Smooth and refined 🥃", "image_file_id": "AgACAgQAAxkBAANWZ_EmWllOXh6S_QFULOwzOIkv2-gAAlXEMRtPHohTbe2vIwqvhUgBAAMCAAN4AAM2BA"},
            {"name": "Jagamastar", "price": 12000, "description": "Energetic spirit ⚡", "image_file_id": "AgACAgQAAxkBAANgZ_EnArHeA2wmxRfNv98Fk8puF1MAAlnEMRtPHohTSaAHcL0tjv0BAAMCAAN4AAM2BA"},
            {"name": "Amarola", "price": 9000, "description": "Sweet cream liqueur 🍬", "image_file_id": "AgACAgQAAxkBAANiZ_EnGsBF9jN4jg594Usd27hCRfAAAlrEMRtPHohTeiK4CivYgWEBAAMCAAN5AAM2BA"},
            {"name": "Gordon", "price": 9000, "description": "Crisp and classic gin 🍸", "image_file_id": "AgACAgQAAxkBAANkZ_EnM8JtVHMmZtMYOp3j7qIVWNsAAlzEMRtPHohTYgKw3ilUe6sBAAMCAAN4AAM2BA"},
            {"name": "Wintar", "price": 7000, "description": "Refreshing vibes ❄️", "image_file_id": "AgACAgQAAxkBAANmZ_EnUoNfUjPH6ZEHqIK03waNVSYAAl3EMRtPHohT0HyRrJqAapwBAAMCAAN5AAM2BA"},
            {"name": "Black ba cc", "price": 600, "description": "Black Label by the cc 🔸", "image_file_id": "AgACAgQAAxkBAANoZ_EnbWg3UVAIIxEvzBm7M7Nyw8cAAl7EMRtPHohTmQiucukCHAwBAAMCAAN4AAM2BA"},
            {"name": "Amarola ba cc", "price": 600, "description": "Amarola by the cc 💧", "image_file_id": "AgACAgQAAxkBAANqZ_Eng5NYoY7ZMoETiUQdYp4FqKkAAl_EMRtPHohTysFVxVhRK6ABAAMCAAN5AAM2BA"},
            {"name": "Gordan ba cc", "price": 500, "description": "Gordon’s gin by cc 🌿", "image_file_id": "AgACAgQAAxkBAANsZ_EnmOr0V86ki7N1_MFQEuRiCm0AAmDEMRtPHohT5JbD5rYL2jcBAAMCAAN4AAM2BA"},
            {"name": "Sambuka (1 shot)", "price": 500, "description": "Anise-flavored shot 🔥", "image_file_id": "AgACAgQAAxkBAANuZ_EnuFxq2EzvjF-CrTk28a7-H4UAAmHEMRtPHohTuTDSsbmvUP8BAAMCAAN4AAM2BA"},
            {"name": "Takila (1 shot)", "price": 500, "description": "Bold tequila shot 🧨", "image_file_id": "AgACAgQAAxkBAANwZ_En0qS3_KaDQs7yyOPpI6Xnr_cAAmLEMRtPHohTR9wIlS7dt9ABAAMCAAN4AAM2BA"},
            {"name": "Hokah", "price": 400, "description": "Smooth smoking 🌀", "image_file_id": "AgACAgQAAxkBAANyZ_En60Ufj0GgHdYf7q6OTBRKFyYAAmPEMRtPHohTBqSNldykgkMBAAMCAANtAAM2BA"},
            {"name": "Red Bull", "price": 600, "description": "Wings incoming 🪽", "image_file_id": "AgACAgQAAxkBAAN0Z_EoC4qzB2MP_NHeapdpcwPWl-AAAmTEMRtPHohTqg7SKIW8C4ABAAMCAAN5AAM2BA"},
            {"name": "Birra", "price": 150, "description": "Local taste 🍻", "image_file_id": "AgACAgQAAxkBAAN2Z_Eoiq8Qg8dUyf-DWWhYBzurXEYAAmbEMRtPHohTXdrBcTVWWkEBAAMCAAN5AAM2BA"},
            {"name": "Water", "price": 100, "description": "Stay hydrated 💧", "image_file_id": "AgACAgQAAxkBAAN4Z_EoqUWzSA9lQLz0wY0mrFg0q0IAAmfEMRtPHohTPhFgjpty0R8BAAMCAAN4AAM2BA"},
        ]
    }
}

BANK_ACCOUNTS = [
    {
        "bank_name": "Commercial Bank of Ethiopia (CBE)",
        "account_holder": "Rahima Kalil",
        "account_number": "1000014828657"
    },
    {
        "bank_name": "Sinqe bank",
        "account_holder": "Rehima Kelli",
        "account_number": "1048094320118"
    }
]

# Start or /menu command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    logger.info(f"Start command used in chat ID: {chat_id}")
    # Clear all previous menu messages
    await clear_previous_menu(chat_id, context)
    # Clear the /start command message itself
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id)
    except Exception as e:
        logger.warning(f"Failed to delete /start message in chat {chat_id}: {e}")
    await show_drinks_menu(chat_id, context)

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    logger.info(f"Menu command used in chat ID: {chat_id}")
    # Clear all previous menu messages
    await clear_previous_menu(chat_id, context)
    # Clear the /menu command message itself
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id)
    except Exception as e:
        logger.warning(f"Failed to delete /menu message in chat {chat_id}: {e}")
    await show_drinks_menu(chat_id, context)

# Show drinks menu
async def show_drinks_menu(chat_id, context):
    drinks = MENU["Drinks"]["items"]
    menu_messages = []

    for idx, item in enumerate(drinks):
        caption = f"🍹 <b>{item['name']}</b>\n💰 <b>Price:</b> ETB {item['price']}\n📝 {item['description']}"
        keyboard = [[InlineKeyboardButton("👀 View Details", callback_data=f"view_Drinks_{idx}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        try:
            msg = await context.bot.send_photo(
                chat_id=chat_id,
                photo=item["image_file_id"],
                caption=caption,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
        except Exception as e:
            logger.warning(f"Photo send failed for {item['name']}: {e}")
            msg = await context.bot.send_message(
                chat_id=chat_id,
                text=caption,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )

        menu_messages.append(msg.message_id)

    # Refresh and back buttons
    action_buttons = [
        [InlineKeyboardButton("🔁 Refresh Menu", callback_data="refresh_menu")],
    ]
    msg = await context.bot.send_message(
        chat_id=chat_id,
        text="👇 Tap to refresh or go back to menu:",
        reply_markup=InlineKeyboardMarkup(action_buttons)
    )
    menu_messages.append(msg.message_id)

    # Save all sent message IDs
    context.user_data["menu_messages"] = menu_messages

# Delete previous menu messages
async def clear_previous_menu(chat_id, context):
    # Delete all previously stored menu messages
    for msg_id in context.user_data.get("menu_messages", []):
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except Exception as e:
            logger.warning(f"Failed to delete message {msg_id} in chat {chat_id}: {e}")
    # Clear the stored message IDs
    context.user_data["menu_messages"] = []

# Account handler
async def account(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    # Clear previous menu messages before showing account info
    await clear_previous_menu(chat_id, context)
    # Delete the /account command message itself
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id)
    except Exception as e:
        logger.warning(f"Failed to delete /account message in chat {chat_id}: {e}")
    # Format the bank account information with icons and copiable account numbers
    account_info = "🏦 Bank Account Information:\n\n"
    for bank in BANK_ACCOUNTS:
        account_info += (
            f"🏛️ Bank: {bank['bank_name']}\n"
            f"👤 Account Holder: {bank['account_holder']}\n"
            f"💳 Account Number: `{bank['account_number']}`\n\n"
        )

    await update.message.reply_text(account_info, parse_mode="Markdown")

# Comment handler
async def comment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    logger.info(f"Comment command used in chat ID: {chat_id}")
    # Clear previous menu messages before prompting for comment
    await clear_previous_menu(chat_id, context)
    # Delete the /comment command message itself
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id)
    except Exception as e:
        logger.warning(f"Failed to delete /comment message in chat {chat_id}: {e}")
    context.user_data["awaiting_comment"] = True
    msg = await context.bot.send_message(chat_id=chat_id, text="💬 Please type your comment below.")
    # Add the comment prompt message to the list to be cleared later
    context.user_data.setdefault("menu_messages", []).append(msg.message_id)

# Message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    user_id = message.from_user.id
    chat_id = message.chat_id

    if message.photo:
        file_id = message.photo[-1].file_id
        # Clear previous menu messages before showing the file ID
        await clear_previous_menu(chat_id, context)
        # Delete the photo message itself
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=message.message_id)
        except Exception as e:
            logger.warning(f"Failed to delete photo message in chat {chat_id}: {e}")
        msg = await context.bot.send_message(
            chat_id=chat_id,
            text=f"📷 Received image!\nFile ID: `{file_id}`",
            parse_mode="Markdown"
        )
        # Add the file ID message to the list to be cleared later
        context.user_data.setdefault("menu_messages", []).append(msg.message_id)
        return

    if context.user_data.get("awaiting_comment", False):
        context.user_data["awaiting_comment"] = False
        feedback = message.text.strip()
        # Clear previous menu messages (including the comment prompt)
        await clear_previous_menu(chat_id, context)
        # Delete the user's feedback message
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=message.message_id)
        except Exception as e:
            logger.warning(f"Failed to delete feedback message in chat {chat_id}: {e}")
        msg = await context.bot.send_message(
            chat_id=STAFF_GROUP_CHAT_ID,
            text=f"💬 Feedback from {user_id}:\n{feedback}"
        )
        # Add the feedback confirmation message to the list to be cleared later
        feedback_msg = await context.bot.send_message(
            chat_id=chat_id,
            text="✅ Thanks for your feedback!"
        )
        context.user_data.setdefault("menu_messages", []).append(feedback_msg.message_id)

# Callback buttons
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    data = query.data

    logger.info(f"Button clicked in chat ID: {chat_id}, callback_data: {data}")

    if data == "refresh_menu" or data == "back_to_menu":
        # Clear all previous menu messages
        await clear_previous_menu(chat_id, context)
        await show_drinks_menu(chat_id, context)
        return

    if data.startswith("view_"):
        # Clear all previous menu messages before showing the item details
        await clear_previous_menu(chat_id, context)
        _, category, idx = data.split("_")
        item = MENU[category]["items"][int(idx)]
        caption = f"🍹 <b>{item['name']}</b>\n💰 <b>Price:</b> ETB {item['price']}\n📝 {item['description']}"

        keyboard = [[InlineKeyboardButton("⬅ Back to Menu", callback_data="back_to_menu")]]
        msg = await context.bot.send_photo(
            chat_id=chat_id,
            photo=item["image_file_id"],
            caption=caption,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        # Add the new message to the list to be cleared later
        context.user_data["menu_messages"] = [msg.message_id]

# Main
if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("account", account))
    app.add_handler(CommandHandler("comment", comment))
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_message))
    app.add_handler(CallbackQueryHandler(button))

    print("🤖 Bot is running...")
    app.run_polling()
