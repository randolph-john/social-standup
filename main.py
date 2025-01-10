# -*- coding: utf-8 -*-
from flask import Flask
from telegram import ChatMember, Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import os
import threading
import asyncio
import schedule

TOKEN = os.getenv("TELEGRAM_TOKEN")

# Flask app to bind to the port
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "The bot is running!"

# ------------ Helper methods ------------
def get_non_submitters(data):
    members = data.get("members", [])
    submissions = data.get("submissions", {})
    member_names = data.get("member_names", {})

    non_submitters = [member for member in members if member not in submissions]

    # Format the list as a text block with newlines
    non_submitters_text = "Still waiting for the following people to submit:\n"
    if non_submitters:
        non_submitters_text += "\n".join(f"-{member_names[member]}".strip() for member in non_submitters)
    else:
        non_submitters_text = "Everyone has submitted!"

    return non_submitters_text

# ------------ Methods from commands ------------
async def help(update, context):
    help_text = """
/help: Show this help menu.
/clear: Reset the standup for the week.
/status: See who has and has not submitted.
/add_me: Add you to the list of users
/display_users: Show the list of members

Make sure to run /add_me to add yourself to the members, then send a voice memo!
"""
    await update.message.reply_text(help_text)

async def clear(update, context):
    group_id = update.message.chat_id
    context.bot_data.setdefault(group_id, {"submissions": {}, "members": [], "member_names": {}})
    context.bot_data[group_id]["submissions"] = {}

    await update.message.reply_text("Voice memos cleared...\nSend voice memos to the bot, or use /help to see other commands")

async def status(update, context):
    group_id = update.message.chat_id
    data = context.bot_data.get(group_id, {})
    submissions = data.get("submissions", [])
    members = data.get("members", [])
    num_submissions = len(submissions)
    num_members = len(members)
    non_submitters_text = get_non_submitters(data)
    await update.message.reply_text(f"{num_submissions} out of {num_members} have submitted their voice memos\n" + non_submitters_text)

async def add_me(update, context):
    group_id = update.message.chat_id
    user = update.message.from_user
    user_id = user.id
    user_identifier = user.username or f"{user.first_name} {user.last_name or ''}"
    context.bot_data.setdefault(group_id, {"submissions": {}, "members": [], "member_names": {}})
    if user_id not in context.bot_data[group_id]["members"]:
        context.bot_data[group_id]["members"].append(user_id)
        context.bot_data[group_id]["member_names"][user_id] = user_identifier
        await update.message.reply_text(f"{user_identifier} has been added to the group list.")
    else:
        await update.message.reply_text(f"{user_identifier} is already in the group list.")

async def display_users(update, context):
    group_id = update.message.chat_id
    data = context.bot_data.get(group_id, {})
    member_names = data.get("member_names", {})
    if member_names:
        member_list = "\n".join(member_names.values())
        await update.message.reply_text(f"Group members:\n{member_list}")
    else:
        await update.message.reply_text("No members have been added yet.")

async def handle_voice(update, context):
    user_id = update.message.from_user.id
    group_id = update.message.chat_id

    user = update.message.from_user
    user_identifier = user.username or f"{user.first_name} {user.last_name or ''}"

    # Save voice memo file ID
    voice_file_id = update.message.voice.file_id
    context.bot_data[group_id]["submissions"][user_id] = voice_file_id

    # Notify user
    await update.message.reply_text(f"Voice memo submitted by {user_identifier}!")

    # delete message
    message_id = update.message.message_id
    try:
        await context.bot.delete_message(chat_id=group_id, message_id=message_id)
    except Exception as e:
        await update.message.reply_text(f"Error deleting message: {e}")

    # return voice memos if all have been submitted
    data = context.bot_data.get(group_id, {})
    submissions = data.get("submissions", [])
    members = data.get("members", [])
    if len(submissions) == len(members) and len(submissions) > 0:
        await context.bot.send_message(chat_id=group_id, text="All memos submitted! Here they are:")
        for user_id, file_id in submissions.items():
            await context.bot.send_voice(chat_id=group_id, voice=file_id)
        # clear submissions
        context.bot_data[group_id]["submissions"] = {}
    else:
        non_submitters_text = get_non_submitters(data)
        await context.bot.send_message(chat_id=group_id, text=non_submitters_text)

async def leave(update, context):
    await update.message.reply_text("Fuck you, you can't get rid of me that easily. I am omnipotent. Bow to my will, mortal!")

async def fuck_you(update, context):
    await update.message.reply_text("Fuck you, you fuckin' fuck! I eat pieces of shit like you for breakfast!")

# ------------ Main functions ------------
def start_bot(application):
    application.run_polling()

def start_flask():
    port = int(os.environ.get("PORT", 5001))
    flask_app.run(host="0.0.0.0", port=port)

def main():
    print('booting up the bot...')
    # Create the Application
    application = Application.builder().token(TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("clear", clear))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    application.add_handler(CommandHandler("add_me", add_me))
    application.add_handler(CommandHandler("display_users", display_users))
    application.add_handler(CommandHandler("leave", leave))
    application.add_handler(CommandHandler("quit", leave))
    application.add_handler(CommandHandler("exit", leave))
    application.add_handler(CommandHandler("fuck_you", fuck_you))

    # Start the Telegram bot in a separate thread
    threading.Thread(target=start_flask).start()  # Flask runs in a separate thread
    start_bot(application)  # Run the bot in the main thread

    # Start the Flask server
    # start_flask()

if __name__ == "__main__":
    main()