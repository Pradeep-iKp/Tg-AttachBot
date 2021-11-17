# Made with python3
# (C) @HKkrish
# Copyright permission under MIT License
# License -> https://github.com/Pradeep-iKp/Tg-AttachBot/blob/main/LICENSE

import os 
import time
import math
import json
import string 
import random
import traceback
import asyncio
import datetime
import aiofiles
from random import choice
from database import Database
import pyrogram
from pyrogram import Client, filters 
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant, UserBannedInChannel, FloodWait, InputUserDeactivated, UserIsBlocked


Bot = Client(
    "Tg-AttachBot",
    bot_token = os.environ["BOT_TOKEN"],
    api_id = int(os.environ["API_ID"]),
    api_hash = os.environ["API_HASH"],
)

BOT_TEXT = """AAMCBQADGQEAAQyn4WGVK-3PMnxeo32IS7NqQ6VllzQRAAKgAwACIPuxVLSXNZW97RNcAQAHbQADIgQ"""
RATE_TEXT = """**⭐ --Give Your Feedback-- ⭐**

🏓 Here is Our Some Useful Bots, hope it will helpful for you. 

✅ [Check Here](https://t.me/HKrrish/10) 

If you like our service please give feedback! We are waiting for your feedback. It will motivate us! 🤗

🌟 [Click Here to Comment](https://bit.ly/3qMPujU)
"""


FORCE_SUBSCRIBE_TEXT = "<code>Sorry Dear You Must Join My Updates Channel for using me 😌😉....</code>"

broadcast_ids = {}
db = Database(os.environ["DATABASE_URL"], "Tg-AttachBot")
BOT_OWNER = int(os.environ["BOT_OWNER"])
UPDATE_CHANNEL = os.environ.get("UPDATE_CHANNEL", "")

async def send_msg(user_id, message):
    try:
        await message.copy(chat_id=user_id)
        return 200, None
    except FloodWait as e:
        await asyncio.sleep(e.x)
        return send_msg(user_id, message)
    except InputUserDeactivated:
        return 400, f"{user_id} : deactivated\n"
    except UserIsBlocked:
        return 400, f"{user_id} : user is blocked\n"
    except PeerIdInvalid:
        return 400, f"{user_id} : user id invalid\n"
    except Exception as e:
        return 500, f"{user_id} : {traceback.format_exc()}\n"



@Bot.on_message(filters.private & filters.command(["start"]))
async def start(bot, update):
    if not await db.is_user_exist(update.from_user.id):
            await db.add_user(update.from_user.id)
    await update.reply_sticker("AAMCBQADGQEAAQyn4WGVK-3PMnxeo32IS7NqQ6VllzQRAAKgAwACIPuxVLSXNZW97RNcAQAHbQADIgQ")


@Bot.on_message(filters.private & filters.command(["review"]))
async def help(bot, update):
    if not await db.is_user_exist(update.from_user.id):
            await db.add_user(update.from_user.id)
    await update.reply_text(
        text=RATE_TEXT,
        disable_web_page_preview=True,
    )


@Bot.on_message(filters.private & filters.command("broadcast") & filters.user(BOT_OWNER) & filters.reply)
async def broadcast(bot, update):
	all_users = await db.get_all_users()
	broadcast_msg = update.reply_to_message
	while True:
	    broadcast_id = ''.join([random.choice(string.ascii_letters) for i in range(3)])
	    if not broadcast_ids.get(broadcast_id):
	        break
	out = await update.reply_text(text=f"Broadcast Started! You will be notified with log file when all the users are notified.")
	start_time = time.time()
	total_users = await db.total_users_count()
	done = 0
	failed = 0
	success = 0
	broadcast_ids[broadcast_id] = dict(total = total_users, current = done, failed = failed, success = success)
	async with aiofiles.open('broadcast.txt', 'w') as broadcast_log_file:
	    async for user in all_users:
	        sts, msg = await send_msg(user_id = int(user['id']), message = broadcast_msg)
	        if msg is not None:
	            await broadcast_log_file.write(msg)
	        if sts == 200:
	            success += 1
	        else:
	            failed += 1
	        if sts == 400:
	            await db.delete_user(user['id'])
	        done += 1
	        if broadcast_ids.get(broadcast_id) is None:
	            break
	        else:
	            broadcast_ids[broadcast_id].update(dict(current = done, failed = failed, success = success))
	if broadcast_ids.get(broadcast_id):
	    broadcast_ids.pop(broadcast_id)
	completed_in = datetime.timedelta(seconds=int(time.time()-start_time))
	await asyncio.sleep(3)
	await out.delete()
	if failed == 0:
	    await update.reply_text(text=f"🌐 Broadcast Completed in `{completed_in}`\n\n👥 Total users : {total_users}.\n\n🔰 Total done : {done},\n✅ Success : {success},\n❗ Failed {failed}.", quote=True)
	else:
	    await update.reply_document(document='broadcast.txt', caption=f"🌐 Broadcast Completed in `{completed_in}`\n\n👥 Total users : {total_users}.\n\n🔰 Total done : {done},\n✅ Success : {success},❗ Failed : {failed}.")
	os.remove('broadcast.txt')


@Bot.on_message(filters.text & filters.private & filters.reply & filters.regex(r'https?://[^\s]+'))
async def attach(bot, update):
    if not await db.is_user_exist(update.from_user.id):
            await db.add_user(update.from_user.id)
    if UPDATE_CHANNEL:
        try:
            user = await bot.get_chat_member(UPDATE_CHANNEL, update.chat.id)
            if user.status == "kicked":
                await update.reply_text(text="You are banned!")
                return
        except UserNotParticipant:
            await update.reply_text(
		  text=FORCE_SUBSCRIBE_TEXT,
		  reply_markup=InlineKeyboardMarkup(
			  [[InlineKeyboardButton(text="😎 Join Channel 😎", url=f"https://telegram.me/{UPDATE_CHANNEL}")]]
		  )
	    )
            return
        except Exception as error:
            print(error)
            await update.reply_text(text="Something wrong. <a href='https://telegram.me/iDeepBot'> Contact </a>.", disable_web_page_preview=True)
            return
    await update.reply_text(
	    text=f"[\u2063]({update.text}){update.reply_to_message.text}",
	    reply_markup=update.reply_to_message.reply_markup
    )


@Bot.on_message(filters.private & filters.command("status"))
async def status(bot, update):
    total_users = await db.total_users_count()
    text = "**--Bot Status--**\n"
    text += f"\n**Total Users :** `{total_users}`"
    await update.reply_text(
        text=text,
        quote=True,
        disable_web_page_preview=True
    )


Bot.run()
