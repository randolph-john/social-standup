# -*- coding: utf-8 -*-
from telegram import ChatMember, Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import os

TOKEN = os.getenv("TELEGRAM_TOKEN")

async def start(update, context):
    group_id = update.message.chat_id
    context.bot_data.setdefault(group_id, {"submissions": {}, "members": []})
    context.bot_data[group_id]["submissions"] = {}

    await update.message.reply_text("Voice memos cleared...")
    await update.message.reply_text("Send voice memos to the bot, or use /help to see other commands")

async def help(update, context):
    help_text = """
Here are the commands for this bot:

/help: Show this help menu.
/start: Reset the standup for the week.
/status: See who has and has not submitted.
/add_me: Add you to the list of users
/display_users: Show the list of members

Send a voice memo to the bot to submit it

Other features I need to implement:
Automated unlocking
Automated reminders to submit
Automated clearing each week
"""
    await update.message.reply_text(help_text) # @jrandolph update with instructions (everyone has to submit their names)

async def status(update, context):
    group_id = update.message.chat_id
    data = context.bot_data.get(group_id, {})
    submissions = data.get("submissions", [])
    members = data.get("members", [])
    num_submissions = len(submissions)
    num_members = len(members)
    await update.message.reply_text(f"{num_submissions} out of {num_members} have submitted their voice memos")

async def add_me(update, context):
    group_id = update.message.chat_id
    user = update.message.from_user
    user_identifier = user.username or f"{user.first_name} {user.last_name or ''}"
    context.bot_data.setdefault(group_id, {"submissions": {}, "members": []})
    if user_identifier not in context.bot_data[group_id]["members"]:
        context.bot_data[group_id]["members"].append(user_identifier)
        await update.message.reply_text(f"{user_identifier} has been added to the group list.")
    else:
        await update.message.reply_text(f"{user_identifier} is already in the group list.")

async def display_users(update, context):
    group_id = update.message.chat_id
    data = context.bot_data.get(group_id, {})
    members = data.get("members", [])
    if members:
        member_list = "\n".join(members)
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
    else:
        await context.bot.send_message(chat_id=group_id, text="Still waiting for the following people to submit:")

def main():
    print('booting up the bot...')
    # Create the Application
    application = Application.builder().token(TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    application.add_handler(CommandHandler("add_me", add_me))
    application.add_handler(CommandHandler("display_users", display_users))

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()
