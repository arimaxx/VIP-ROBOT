from pyrogram import Client, filters
from pyrogram import Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
from MukeshRobot.modules.connection import connected

# ... other initialization code ...


blacklist_keywords = []

sudo_users = [6352061770]  

muted_users = {}

# -----------------------------------------------------

@app.on_edited_message(filters.group & ~filters.me)
async def delete_edited_messages(client, edited_message):
    await edited_message.delete()

# -------------------------------

async def delete_pdf_files(client, message):
    # Check if the message has reactions
    if message.replies and message.replies.fwd_from:
        # Skip deletion if the message has reactions
        return

    if message.document and message.document.mime_type == "application/pdf":
        warning_message = f"@{message.from_user.username} ᴍᴀᴀ ᴍᴀᴛ ᴄʜᴜᴅᴀ ᴘᴅғ ʙʜᴇᴊ ᴋᴇ,\n ʙʜᴏsᴀᴅɪᴋᴇ ᴄᴏᴘʏʀɪɢʜᴛ ʟᴀɢʏᴇɢᴀ \n\n ᴅᴇʟᴇᴛᴇ ᴋᴀʀ ᴅɪʏᴀ ᴍᴀᴅᴀʀᴄʜᴏᴅ.\n\n ᴀʙ || @lll_notookk_lll || ʙʜᴀɪ ᴋᴇ ᴅᴍ ᴍᴇ ᴀᴘɴɪ ᴍᴜᴍᴍʏ ᴋᴏ ʙʜᴇᴊ ᴅᴇ 🍌🍌🍌."
        await message.reply_text(warning_message)
        await message.delete()
        await notify_and_mute_user(client, message.from_user.id, message.chat.id)
    else:
        for keyword in blacklist_keywords:
            if keyword.lower() in message.text.lower():
                await message.delete()
                await notify_and_mute_user(client, message.from_user.id, message.chat.id)
                break

async def notify_and_mute_user(client, user_id, chat_id):
    if user_id not in muted_users:
        muted_users[user_id] = asyncio.get_event_loop().time() + 3600  # Mute for 1 hour

        admins = await app.get_chat_members(chat_id, filter="administrators")
        admin_ids = [admin.user.id for admin in admins]

        admin_notification = f"🚨 User {user_id} has been muted for 1 hour. 🚨"
        for admin_id in admin_ids:
            await app.send_message(admin_id, admin_notification)

        mute_notification = (
            f"🤐 You have been muted for 1 hour. 🤐\n"
            "Contact the admin to appeal the mute."
        )
        await app.send_message(user_id, mute_notification)

        await app.restrict_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            permissions=app.ChatPermissions(),
            until_date=int(muted_users[user_id])
        )

        # Send unmute button to admin
        for admin_id in admin_ids:
            await app.send_message(
                admin_id,
                f"⚠️ User {user_id} is muted. Click the button to unmute them. ⚠️",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Unmute", callback_data=f"unmute_{user_id}_{chat_id}")]
                ])
            )

# Command to add a word to the blacklist (only sudo users can use this command)
@app.on_message(filters.group & filters.command("blacklist", prefixes="/") & filters.user(sudo_users))
async def add_to_blacklist(client, message):
    if len(message.command) > 1:
        new_keyword = message.command[1].lower()
        if new_keyword not in blacklist_keywords:
            blacklist_keywords.append(new_keyword)
            await message.reply_text(f"Added '{new_keyword}' to the blacklist.")
        else:
            await message.reply_text(f"'{new_keyword}' is already in the blacklist.")
    else:
        await message.reply_text("Please provide a word to add to the blacklist.")

# Command to add a user to sudo users (only the first sudo user can use this command)
@app.on_message(filters.group & filters.command("addsudo", prefixes="/") & filters.user(sudo_users))
async def add_sudo_user(client, message):
    if len(message.command) > 1:
        user_identifier = message.command[1]
        new_sudo_user = await client.get_users(user_identifier)
        
        if new_sudo_user.id not in sudo_users:
            sudo_users.append(new_sudo_user.id)
            await message.reply_text(f"Added user {new_sudo_user.username} to sudo users.")
        else:
            await message.reply_text(f"User {new_sudo_user.username} is already a sudo user.")
    else:
        await message.reply_text("Please provide a user ID or username to add as a sudo user.")

# Callback to handle the unmute button click
@app.on_callback_query(filters.regex(r"^unmute_(\d+)_(\d+)$"))
async def handle_unmute_button(_, callback_query):
    user_id = int(callback_query.matches[0].group(1))
    chat_id = int(callback_query.matches[0].group(2))
    
    if callback_query.from_user.id in await app.get_chat_administrators(chat_id):
        if user_id in muted_users:
            await app.restrict_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                permissions=app.ChatPermissions(),
                until_date=0  # Unmute
            )

            del muted_users[user_id]

            await callback_query.answer("User unmuted successfully.")
            await callback_query.message.delete()
        else:
            await callback_query.answer("User is not muted.")
    else:
        await callback_query.answer("You do not have the authority to unmute.")
