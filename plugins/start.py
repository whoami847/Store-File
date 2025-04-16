import os
import re, sys
import json
import base64
import logging
import random
import asyncio
import time
import pytz
from database.verify_db import vr_db
from .pmfilter import auto_filter 
from Script import script
from datetime import datetime
from database.refer import referdb
from database.config_db import mdb
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait
from pyrogram.types import *
from database.ia_filterdb import Media, Media2, get_file_details, unpack_new_file_id, get_bad_files
from database.users_chats_db import db, delete_all_msg
from utils import *
from database.connections_mdb import active_connection

# Set up logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

TIMEZONE = "Asia/Kolkata"
BATCH_FILES = {}

# Default reactions list since info.py is not available
REACTIONS = ["❤️", "👍", "🔥", "🎉", "😍"]

@Client.on_message(filters.command("start") & filters.incoming)
async def start(client, message):
    # Add reaction emoji directly without checking EMOJI_MODE
    await message.react(emoji=random.choice(REACTIONS), big=True) 
    if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        buttons = [[
                    InlineKeyboardButton('• ᴀᴅᴅ ᴍᴇ ᴛᴏ ᴜʀ ᴄʜᴀᴛ •', url=f'http://t.me/{temp.U_NAME}?startgroup=true')
                ],[
                    InlineKeyboardButton('• ᴍᴀsᴛᴇʀ •', url="https://t.me/cosmic_freak"),
                    InlineKeyboardButton('• sᴜᴘᴘᴏʀᴛ •', url='https://t.me/codeflixsupport')
                ],[
                    InlineKeyboardButton('• ᴊᴏɪɴ ᴜᴘᴅᴀᴛᴇs ᴄʜᴀɴɴᴇʟ •', url="https://t.me/codeflix_bots")
                  ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply(script.GSTART_TXT.format(message.from_user.mention if message.from_user else message.chat.title, temp.U_NAME, temp.B_NAME), reply_markup=reply_markup, disable_web_page_preview=True)
        await asyncio.sleep(2) 
        if not await db.get_chat(message.chat.id):
            total=await client.get_chat_members_count(message.chat.id)
            await client.send_message(LOG_CHANNEL, script.LOG_TEXT_G.format(message.chat.title, message.chat.id, total, "Unknown"))       
            await db.add_chat(message.chat.id, message.chat.title)
        return 
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)
        await client.send_message(LOG_CHANNEL, script.LOG_TEXT_P.format(message.from_user.id, message.from_user.mention))
    if len(message.command) != 2:
        buttons = [[
                    InlineKeyboardButton(text="🏡", callback_data="start"),
                    InlineKeyboardButton(text="🛡", callback_data="group_info"),
                    InlineKeyboardButton(text="💳", callback_data="about"),
                    InlineKeyboardButton(text="💸", callback_data="shortlink_info"),
                    InlineKeyboardButton(text="🖥", callback_data="main"),
                ],[
                    InlineKeyboardButton('ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ', url=f'http://t.me/{temp.U_NAME}?startgroup=true')
                ],[
                    InlineKeyboardButton('• ᴄᴏᴍᴍᴀɴᴅꜱ •', callback_data='main'),
                    InlineKeyboardButton('• ᴇᴀʀɴ ᴍᴏɴᴇʏ •', callback_data='shortlink_info')
                ],[
                    InlineKeyboardButton('• ᴘʀᴇᴍɪᴜᴍ •', callback_data='premium_info'),
                    InlineKeyboardButton('• ᴀʙᴏᴜᴛ •', callback_data='about')
                  ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        current_time = datetime.now(pytz.timezone(TIMEZONE))
        curr_time = current_time.hour        
        if curr_time < 12:
            gtxt = "ɢᴏᴏᴅ ᴍᴏʀɴɪɴɢ 👋" 
        elif curr_time < 17:
            gtxt = "ɢᴏᴏᴅ ᴀғᴛᴇʀɴᴏᴏɴ 👋" 
        elif curr_time < 21:
            gtxt = "ɢᴏᴏᴅ ᴇᴠᴇɴɪɴɢ 👋"
        else:
            gtxt = "ɢᴏᴏᴅ ɴɪɢʜᴛ 👋"
        m=await message.reply_text("<i>ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ <b>ʟᴜᴄʏ</b>.\nʜᴏᴘᴇ ʏᴏᴜ'ʀᴇ ᴅᴏɪɴɢ ᴡᴇʟʟ...</i>")
        await asyncio.sleep(0.4)
        await m.edit_text("⏳")
        await asyncio.sleep(0.5)
        await m.edit_text("👀")
        await asyncio.sleep(0.5)
        await m.edit_text("<b><i>ꜱᴛᴀʀᴛɪɴɢ...</i></b>")
        await asyncio.sleep(0.4)
        await m.delete()        
        m=await message.reply_sticker("CAACAgUAAxkBAAJFeWd037UWP-vgb_dWo55DCPZS9zJzAAJpEgACqXaJVxBrhzahNnwSHgQ") 
        await asyncio.sleep(1)
        await m.delete()
        await message.reply_photo(
            photo=random.choice(PICS),
            caption=script.START_TXT.format(message.from_user.mention, gtxt, temp.U_NAME, temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        return
    
    if not await db.has_premium_access(message.from_user.id):
        channels = (await get_settings(int(message.from_user.id))).get('fsub')
        if channels:  
            btn = await is_subscribed(client, message, channels)
            if btn:
                kk, file_id = message.command[1].split("_", 1)
                btn.append([InlineKeyboardButton("ᴛʀʏ ᴀɢᴀɪɴ", callback_data=f"checksub#{kk}#{file_id}")])
                reply_markup = InlineKeyboardMarkup(btn)
                caption = (
                    f"**ᴊᴏɪɴ ᴏᴜʀ ᴜᴘᴅᴀᴛᴇꜱ ᴄʜᴀɴɴᴇʟ ᴀɴᴅ ᴛʜᴇɴ ᴄʟɪᴄᴋ ᴏɴ ᴛʀʏ ᴀɢᴀɪɴ ᴛᴏ ɢᴇᴛ ʏᴏᴜʀ ʀᴇǫᴜᴇꜱᴛᴇᴅ ꜰɪʟᴇ.**"
                )
                await message.reply_photo(
                    photo=random.choice(FSUB_PICS),
                    caption=caption,
                    reply_markup=reply_markup,
                    parse_mode=enums.ParseMode.HTML
                )
                return
       
    if len(message.command) == 2 and message.command[1] in ["subscribe", "error", "okay", "help"]:
        buttons = [[
                    InlineKeyboardButton(text="🏡", callback_data="start"),
                    InlineKeyboardButton(text="🛡", callback_data="group_info"),
                    InlineKeyboardButton(text="💳", callback_data="about"),
                    InlineKeyboardButton(text="💸", callback_data="shortlink_info"),
                    InlineKeyboardButton(text="🖥", callback_data="main"),
                ],[
                    InlineKeyboardButton('ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ', url=f'http://t.me/{temp.U_NAME}?startgroup=true')
                ],[
                    InlineKeyboardButton('• ᴄᴏᴍᴍᴀɴᴅꜱ •', callback_data='main'),
                    InlineKeyboardButton('• ᴇᴀʀɴ ᴍᴏɴᴇʏ •', callback_data='shortlink_info')
                ],[
                    InlineKeyboardButton('• ᴘʀᴇᴍɪᴜᴍ •', callback_data='premium_info'),
                    InlineKeyboardButton('• ᴀʙᴏᴜᴛ •', callback_data='about')
                  ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        current_time = datetime.now(pytz.timezone(TIMEZONE))
        curr_time = current_time.hour        
        if curr_time < 12:
            gtxt = "ɢᴏᴏᴅ ᴍᴏʀɴɪɴɢ 👋" 
        elif curr_time < 17:
            gtxt = "ɢᴏᴏᴅ ᴀғᴛᴇʀɴᴏᴏɴ 👋" 
        elif curr_time < 21:
            gtxt = "ɢᴏᴏᴅ ᴇᴠᴇɴɪɴɢ 👋"
        else:
            gtxt = "ɢᴏᴏᴅ ɴɪɢʜᴛ 👋"
        m=await message.reply_text("ʜᴇʟʟᴏ ʙᴀʙʏ, ʜᴏᴡ ᴀʀᴇ ʏᴏᴜ \nᴡᴀɪᴛ ᴀ ᴍᴏᴍᴇɴᴛ ʙᴀʙʏ . . .")
        await asyncio.sleep(0.4)
        await m.edit_text("🎊")
        await asyncio.sleep(0.5)
        await m.edit_text("⚡")
        await asyncio.sleep(0.5)
        await m.edit_text("ꜱᴛᴀʀᴛɪɴɢ ʙᴀʙʏ...")
        await asyncio.sleep(0.4)
        await m.delete()        
        m=await message.reply_sticker("CAACAgUAAxkBAAECroBmQKMAAQ-Gw4nibWoj_pJou2vP1a4AAlQIAAIzDxlVkNBkTEb1Lc4eBA") 
        await asyncio.sleep(1)
        await m.delete()
        await message.reply_photo(
            photo=random.choice(PICS),
            caption=script.START_TXT.format(message.from_user.mention, gtxt, temp.U_NAME, temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        return
    if message.command[1].startswith("reff_"):
        try:
            user_id = int(message.command[1].split("_")[1])
        except ValueError:
            await message.reply_text("Invalid refer!")
            return
        if user_id == message.from_user.id:
            await message.reply_text("Hᴇʏ Dᴜᴅᴇ, Yᴏᴜ Cᴀɴ'ᴛ Rᴇғᴇʀ Yᴏᴜʀsᴇʟғ 🤣!\n\nsʜᴀʀᴇ ʟɪɴᴋ ʏᴏᴜʀ ғʀɪᴇɴᴅ ᴀɴᴅ ɢᴇᴛ 10 ʀᴇғᴇʀʀᴀʟ ᴘᴏɪɴᴛ ɪғ ʏᴏᴜ ᴀʀᴇ ᴄᴏʟʟᴇᴄᴛɪɴɢ 100 ʀᴇғᴇʀʀᴀʟ ᴘᴏɪɴᴛs ᴛʜᴇɴ ʏᴏᴜ ᴄᴀɴ ɢᴇᴛ 1 ᴍᴏɴᴛʜ ғʀᴇᴇ ᴘʀᴇᴍɪᴜᴍ ᴍᴇᴍʙᴇʀsʜɪᴘ.")
            return
        if referdb.is_user_in_list(message.from_user.id):
            await message.reply_text("Yᴏᴜ ʜᴀᴠᴇ ʙᴇᴇɴ ᴀʟʀᴇᴀᴅʏ ɪɴᴠɪᴛᴇᴅ ❗")
            return
        try:
            uss = await client.get_users(user_id)
        except Exception:
            return 	    
        referdb.add_user(message.from_user.id)
        fromuse = referdb.get_refer_points(user_id) + 10
        if fromuse == 100:
            referdb.add_refer_points(user_id, 0) 
            await message.reply_text(f"🎉 𝗖𝗼𝗻𝗴𝗿𝗮𝘁𝘂𝗹𝗮𝘁𝗶𝗼𝗻𝘀! 𝗬𝗼𝘂 𝘄𝗼𝗻 𝟭𝟬 𝗥𝗲𝗳𝗲𝗿𝗿𝗮𝗹 𝗽𝗼𝗶𝗻𝘁 𝗯𝗲𝗰𝗮𝘂𝘀𝗲 𝗬𝗼𝘂 𝗵𝗮𝘃𝗲 𝗯𝗲𝗲𝗻 𝗦𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆 𝗜𝗻𝘃𝗶𝘁𝗲𝗱 ☞ {uss.mention}!")		    
            await message.reply_text(user_id, f"You have been successfully invited by {message.from_user.mention}!") 	
            seconds = 2592000
            if seconds > 0:
                expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
                user_data = {"id": user_id, "expiry_time": expiry_time}  # Using "id" instead of "user_id"  
                await db.update_user(user_data)  # Use the update_user method to update or insert user data		    
                await client.send_message(
                chat_id=user_id,
                text=f"<b>Hᴇʏ {uss.mention}\n\nYᴏᴜ ɢᴏᴛ 1 ᴍᴏɴᴛʜ ᴘʀᴇᴍɪᴜᴍ sᴜʙsᴄʀɪᴘᴛɪᴏɴ ʙʏ ɪɴᴠɪᴛɪɴɢ 10 ᴜsᴇʀs ❗", disable_web_page_preview=True              
                )
            for admin in ADMINS:
                await client.send_message(chat_id=admin, text=f"Sᴜᴄᴄᴇss ғᴜʟʟʏ ᴛᴀsᴋ ᴄᴏᴍᴘʟᴇᴛᴇᴅ ʙʏ ᴛʜɪs ᴜsᴇʀ:\n\nuser Nᴀᴍᴇ: {uss.mention}\n\nUsᴇʀ ɪᴅ: {uss.id}!")	
        else:
            referdb.add_refer_points(user_id, fromuse)
            await message.reply_text(f"You have been successfully invited by {uss.mention}!")
            await client.send_message(user_id, f"𝗖𝗼𝗻𝗴𝗿𝗮𝘁𝘂𝗹𝗮𝘁𝗶𝗼𝗻𝘀! 𝗬𝗼𝘂 𝘄𝗼𝗻 𝟭𝟬 𝗥𝗲𝗳𝗲𝗿𝗿𝗮𝗹 𝗽𝗼𝗶𝗻𝘁 𝗯𝗲𝗰𝗮𝘂𝘀𝗲 𝗬𝗼𝘂 𝗵𝗮𝘃𝗲 𝗯𝗲𝗲𝗻 𝗦𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆 𝗜𝗻𝘃𝗶𝘁𝗲𝗱 ☞{message.from_user.mention}!")
        return
        
    if len(message.command) == 2 and message.command[1] in ["premium"]:
        buttons = [[
                    InlineKeyboardButton('📲 ꜱᴇɴᴅ ᴘᴀʏᴍᴇɴᴛ ꜱᴄʀᴇᴇɴꜱʜᴏᴛ', url=OWNER_LNK)
                  ],[
                    InlineKeyboardButton('❌ ᴄʟᴏꜱᴇ ❌', callback_data='close_data')
                  ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply_photo(
            photo=(SUBSCRIPTION),
            caption=script.PREPLANS_TXT.format(message.from_user.mention, OWNER_UPI_ID, QR_CODE),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        return  
    if len(message.command) == 2 and message.command[1].startswith('getfile'):
        movies = message.command[1].split("-", 1)[1] 
        movie = movies.replace('-',' ')
        message.text = movie 
        await auto_filter(client, message) 
        return
    
    data = message.command[1]
    try:
        pre, file_id = data.split('_', 1)
    except:
        file_id = data
        pre = ""

    if data.split("-", 1)[0] == "BATCH":
        sts = await message.reply("<b>Please wait...</b>")
        file_id = data.split("-", 1)[1]
        msgs = BATCH_FILES.get(file_id)
        if not msgs:
            file = await client.download_media(file_id)
            try:
                with open(file) as file_data:
                    msgs = json.loads(file_data.read())
            except:
                await sts.edit("FAILED")
                return await client.send_message(LOG_CHANNEL, "UNABLE TO OPEN FILE.")
            os.remove(file)
            BATCH_FILES[file_id] = msgs

        for msg in msgs:
            title = msg.get("title")
            size = get_size(int(msg.get("size", 0)))
            f_caption = msg.get("caption", "")

            if BATCH_FILE_CAPTION:
                try:
                    f_caption = BATCH_FILE_CAPTION.format(file_name='' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)
                except Exception as e:
                    logger.exception(e)
                    f_caption = f_caption

            if f_caption is None:
                f_caption = f"{title}"

            if STREAM_MODE:
                btn = [
                    [InlineKeyboardButton('🚀 ꜰᴀꜱᴛ ᴅᴏᴡɴʟᴏᴀᴅ / ᴡᴀᴛᴄʜ ᴏɴʟɪɴᴇ 🖥️', callback_data=f'generate_stream_link:{file_id}')],
                    [InlineKeyboardButton('📌 ᴊᴏɪɴ ᴜᴘᴅᴀᴛᴇꜱ ᴄʜᴀɴɴᴇʟ 📌', url=MOVIE_UPDATE_CHANNEL_LNK)]  # Keep this line unchanged
                ]
            else:
                btn = [
                    [InlineKeyboardButton('📌 ᴊᴏɪɴ ᴜᴘᴅᴀᴛᴇꜱ ᴄʜᴀɴɴᴇʟ 📌', url=MOVIE_UPDATE_CHANNEL_LNK)]
                ]
            try:
                await client.send_cached_media(
                    chat_id=message.from_user.id,
                    file_id=msg.get("file_id"),
                    caption=f_caption,
                    protect_content=msg.get('protect', False),
                    reply_markup=InlineKeyboardMarkup(btn)
                )
            except FloodWait as e:
                await asyncio.sleep(e.x)
                logger.warning(f"Floodwait of {e.x} sec.")
                await client.send_cached_media(
                    chat_id=message.from_user.id,
                    file_id=msg.get("file_id"),
                    caption=f_caption,
                    protect_content=msg.get('protect', False),
                    reply_markup=InlineKeyboardMarkup(btn)
                )
            except Exception as e:
                logger.warning(e, exc_info=True)
                continue
            await asyncio.sleep(1)

        await sts.delete()
        return


    elif data.split("-", 1)[0] == "DSTORE":
        sts = await message.reply("<b>Please wait...</b>")
        b_string = data.split("-", 1)[1]
        decoded = (base64.urlsafe_b64decode(b_string + "=" * (-len(b_string) % 4))).decode("ascii")
        try:
            f_msg_id, l_msg_id, f_chat_id, protect = decoded.split("_", 3)
        except:
            f_msg_id, l_msg_id, f_chat_id = decoded.split("_", 2)
            protect = "/pbatch" if PROTECT_CONTENT else "batch"
        diff = int(l_msg_id) - int(f_msg_id)
        async for msg in client.iter_messages(int(f_chat_id), int(l_msg_id), int(f_msg_id)):
            if msg.media:
                media = getattr(msg, msg.media.value)
                if BATCH_FILE_CAPTION:
                    try:
                        f_caption=BATCH_FILE_CAPTION.format(file_name=getattr(media, 'file_name', ''), file_size=getattr(media, 'file_size', ''), file_caption=getattr(msg, 'caption', ''))
                    except Exception as e:
                        logger.exception(e)
                        f_caption = getattr(msg, 'caption', '')
                else:
                    media = getattr(msg, msg.media.value)
                    file_name = getattr(media, 'file_name', '')
                    f_caption = getattr(msg, 'caption', file_name)
                try:
                    await msg.copy(message.chat.id, caption=f_caption, protect_content=True if protect == "/pbatch" else False)
                except FloodWait as e:
                    await asyncio.sleep(e.x)
                    await msg.copy(message.chat.id, caption=f_caption, protect_content=True if protect == "/pbatch" else False)
                except Exception as e:
                    logger.exception(e)
                    continue
            elif msg.empty:
                continue
            else:
                try:
                    await msg.copy(message.chat.id, protect_content=True if protect == "/pbatch" else False)
                except FloodWait as e:
                    await asyncio.sleep(e.x)
                    await msg.copy(message.chat.id, protect_content=True if protect == "/pbatch" else False)
                except Exception as e:
                    logger.exception(e)
                    continue
            await asyncio.sleep(1) 
        return await sts.delete()

    elif data.split("-", 1)[0] == "verify":
        userid = data.split("-", 2)[1]
        token = data.split("-", 3)[2] 
        fileid = data.split("-", 3)[3]
        if str(message.from_user.id) != str(userid):
            return await message.reply_text(
                text="<b>Invalid link or Expired link !</b>",
                protect_content=False
            )
        is_valid = await check_token(client, userid, token)
        if is_valid == True:
            btn = [[
                InlineKeyboardButton("ᴄʟɪᴄᴋ ʜᴇʀᴇ ᴛᴏ ɢᴇᴛ ғɪʟᴇ", url=f"https://telegram.me/{temp.U_NAME}?start=files_{fileid}")
            ]]
            await message.reply_photo(
                photo="https://graph.org/file/6928de1539e2e80e47fb8.jpg",
                caption=f"<blockquote><b>👋 ʜᴇʏ {message.from_user.mention}, ʏᴏᴜ'ʀᴇ ᴀʀᴇ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴠᴇʀɪꜰɪᴇᴅ ✅\n\nɴᴏᴡ ʏᴏᴜ'ᴠᴇ ᴜɴʟɪᴍɪᴛᴇᴅ ᴀᴄᴄᴇꜱꜱ ғᴏʀ {VERIFY_EXPIRE} ʜᴏᴜʀs🎉</blockquote></b>",
                reply_markup=InlineKeyboardMarkup(btn)
            )
            await verify_user(client, userid, token) 
            await vr_db.save_verification(message.from_user.id) 
            now = datetime.now()
            current_time = now.strftime("%H:%M:%S")
            current_date = now.strftime("%Y-%m-d")
            
            lucy_message = (
                f"Name: {message.from_user.mention}\n"
                f"Time: {current_time}\n"
                f"Date: {current_date}\n"
                f"#verify_completed"
            )
            await client.send_message(chat_id=VERIFIED_LOG, text=lucy_message)

        else:
            return await message.reply_text(
                text="<b>Invalid link or Expired link !</b>",
                protect_content=False
            )
    if data.startswith("sendfiles"):
        current_time = datetime.now(pytz.timezone(TIMEZONE))
        curr_time = current_time.hour        
        if curr_time < 12:
            gtxt = "ɢᴏᴏᴅ ᴍᴏʀɴɪɴɢ 👋" 
        elif curr_time < 17:
            gtxt = "ɢᴏᴏᴅ ᴀғᴛᴇʀɴᴏᴏɴ 👋" 
        elif curr_time < 21:
            gtxt = "ɢᴏᴏᴅ ᴇᴠᴇɴɪɴɢ 👋"
        else:
            gtxt = "ɢᴏᴏᴅ ɴɪɢʜᴛ 👋"
        chat_id = int("-" + file_id.split("-")[1])
        userid = message.from_user.id if message.from_user else None
        g = await get_shortlink(chat_id, f"https://telegram.me/{temp.U_NAME}?start=allfiles_{file_id}")
        k = await client.send_message(chat_id=message.from_user.id,text=f"🫂 ʜᴇʏ {message.from_user.mention}, {gtxt}\n\n‼️ ɢᴇᴛ ᴀʟʟ ꜰɪʟᴇꜱ ɪɴ ᴀ ꜱɪɴɢʟᴇ ʟɪɴᴋ ‼️\n\n✅ ʏᴏᴜʀ ʟɪɴᴋ ɪꜱ ʀᴇᴀᴅʏ, ᴋɪɴᴅʟʏ ᴄʟɪᴄᴋ ᴏɴ ᴅᴏᴡɴʟᴏᴀᴅ ʙᴜᴛᴛᴏɴ.\n\n<u>⚠️ ɴᴏᴛᴇ :- ᴛʜɪꜱ ᴍᴇꜱꜱᴀɢᴇ ɪꜱ ᴅᴇʟᴇᴛᴇᴅ ɪɴ 5 ᴍɪɴᴜᴛᴇꜱ ᴛᴏ ᴀᴠᴏɪᴅ ᴄᴏᴘʏʀɪɢʜᴛ..ꜱᴀᴠᴇ ᴛʜɪꜱ ʟɪɴᴋ ᴛᴏ ꜱᴏᴍᴇᴡʜᴇʀᴇ ᴇʟꜱᴇ</u>", reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton('📁 ᴅᴏᴡɴʟᴏᴀᴅ 📁', url=g)
                    ], [
                        InlineKeyboardButton('⚡ ʜᴏᴡ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ ⚡', url=await get_tutorial(chat_id))
                    ]
                ]
            )
        )
        await asyncio.sleep(300)
        await k.edit("<b>ʏᴏᴜʀ ᴍᴇꜱꜱᴀɢᴇ ɪꜱ ᴅᴇʟᴇᴛᴇᴅ !\nᴋɪɴᴅʟʏ ꜱᴇᴀʀᴄʜ ᴀɢᴀɪɴ.</b>")
        return
        
    elif data.startswith("short"):
        current_time = datetime.now(pytz.timezone(TIMEZONE))
        curr_time = current_time.hour        
        if curr_time < 12:
            gtxt = "ɢᴏᴏᴅ ᴍᴏʀɴɪɴɢ 👋" 
        elif curr_time < 17:
            gtxt = "ɢᴏᴏᴅ ᴀғᴛᴇʀɴᴏᴏɴ 👋" 
        elif curr_time < 21:
            gtxt = "ɢᴏᴏᴅ ᴇᴠᴇɴɪɴɢ 👋"
        else:
            gtxt = "ɢᴏᴏᴅ ɴɪɢʜᴛ 👋"        
        user_id = message.from_user.id
        if await db.has_premium_access(message.from_user.id):
            pass
        else:
            chat_id = temp.SHORT.get(user_id)
            files_ = await get_file_details(file_id)
            files = files_[0]
            g = await get_shortlink(chat_id, f"https://telegram.me/{temp.U_NAME}?start=file_{file_id}")
            k = await client.send_message(chat_id=user_id,text=f"🫂 ʜᴇʏ {message.from_user.mention}, {gtxt}\n\n✅ ʏᴏᴜʀ ʟɪɴᴋ ɪꜱ ʀᴇᴀᴅʏ, ᴋɪɴᴅʟʏ ᴄʟɪᴄᴋ ᴏɴ ᴅᴏᴡɴʟᴏᴀᴅ ʙᴜᴛᴛᴏɴ.\n\n⚠️ ꜰɪʟᴇ ɴᴀᴍᴇ : <code>{files.file_name}</code> \n\n📥 ꜰɪʟᴇ ꜱɪᴢᴇ : <code>{get_size(files.file_size)}</code>\n\n<u>⚠️ ɴᴏᴛᴇ :- ᴛʜɪꜱ ᴍᴇꜱꜱᴀɢᴇ ɪꜱ ᴅᴇʟᴇᴛᴇᴅ ɪɴ 10 ᴍɪɴᴜᴛᴇꜱ ᴛᴏ ᴀᴠᴏɪᴅ ᴄᴏᴘʏʀɪɢʜᴛ..ꜱᴀᴠᴇ ᴛʜɪꜱ ʟɪɴᴋ ᴛᴏ ꜱᴏᴍᴇᴡʜᴇʀᴇ ᴇʟꜱᴇ</u>", reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton('📁 ᴅᴏᴡɴʟᴏᴀᴅ 📁', url=g)
                        ], [
                            InlineKeyboardButton('⚡ ʜᴏᴡ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ ⚡', url=await get_tutorial(chat_id))
                        ]
                    ]
                )
            )
            await asyncio.sleep(600)
            await k.edit("<b>ʏᴏᴜʀ ᴍᴇꜱꜱᴀɢᴇ ɪꜱ ᴅᴇʟᴇᴛᴇᴅ !\nᴋɪɴᴅʟʏ ꜱᴇᴀʀᴄʜ ᴀɢᴀɪɴ.</b>")
            return    
    elif data.startswith("all"):
        files = temp.GETALL.get(file_id)
        if not files:
            return await message.reply('<b><i>ɴᴏ ꜱᴜᴄʜ ꜀ɪʟᴇ ᴇxɪꜱᴛꜱ !</b></i>')
        filesarr = []
        for file in files:
            file_id = file.file_id
            files_ = await get_file_details(file_id)
            files1 = files_[0]
            title = ' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@') and not x.startswith('www.'), files1.file_name.split()))
            size = get_size(files1.file_size)
            f_caption = files1.caption

            if CUSTOM_FILE_CAPTION:
                try:
                    f_caption=CUSTOM_FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)
                except Exception as e:
                    logger.exception(e)
                    f_caption = f_caption

            if f_caption is None:
                f_caption = f"{' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@') and not x.startswith('www.'), files1.file_name.split()))}"
            if await db.has_premium_access(message.from_user.id):
                pass  
            else:
                if not await check_verification(client, message.from_user.id) and VERIFY == True:
                    btn = [[
                       InlineKeyboardButton("ᴄʟɪᴄᴋ ʜᴇʀᴇ ᴛᴏ ᴠᴇʀɪғʏ", url=await get_token(client, message.from_user.id, f"https://telegram.me/{temp.U_NAME}?start=", file_id))
                       ],[
                       InlineKeyboardButton("ʜᴏᴡ ᴛᴏ ᴠᴇʀɪғʏ", url=HOW_TO_VERIFY)
                   ]]
                    l = await message.reply_text(
                        text=f"<blockquote><b>ʜᴇʏ ʙʀᴏ,\n\n ‼️ ʏᴏᴜ'ʀᴇ ɴᴏᴛ ᴠᴇʀɪғɪᴇᴅ ᴛᴏᴅᴀʏ ‼️\n\n ›› ᴘʟᴇᴀsᴇ ᴠᴇʀɪғʏ ᴀɴᴅ ɢᴇᴛ ᴜɴʟɪᴍɪᴛᴇᴅ ᴀᴄᴄᴇss ғᴏʀ {VERIFY_EXPIRE} ʜᴏᴜʀs ✅</blockquote></b>",
                        protect_content=False,
                        reply_markup=InlineKeyboardMarkup(btn)
                    )
                    await asyncio.sleep(180)
                    await l.delete()
                    return
            if STREAM_MODE:
                btn = [
                    [InlineKeyboardButton('🚀 ꜰᴀꜱᴛ ᴅᴏᴡɴʟᴏᴀᴅ / ᴡᴀᴛᴄʜ ᴏɴʟɪɴᴇ 🖥️', callback_data=f'generate_stream_link:{file_id}')],
                    [InlineKeyboardButton('📌 ᴊᴏɪɴ ᴜᴘᴅᴀᴛᴇꜱ ᴄʜᴀɴɴᴇʟ 📌', url=MOVIE_UPDATE_CHANNEL_LNK)]  # Keep this line unchanged  
                ]
            else:
                btn = [
                    [InlineKeyboardButton('📌 ᴊᴏɪɴ ᴜᴘᴅᴀᴛᴇꜱ ᴄʜᴀɴɴᴇʟ 📌', url=MOVIE_UPDATE_CHANNEL_LNK)]
                ]

            msg = await client.send_cached_media(
                chat_id=message.from_user.id,
                file_id=file_id,
                caption=f_caption,
                protect_content=True if pre == 'filep' else False,
                reply_markup=InlineKeyboardMarkup(btn)
            )
            filesarr.append(msg)
        k = await client.send_message(chat_id=message.from_user.id, text=f"<b><u>❗️❗️❗️IMPORTANT❗️️❗️❗️</u></b>\n\nᴛʜɪꜱ ᴍᴏᴠɪᴇ ꜀ɪʟᴇ/ᴠɪᴅᴇᴏ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ ɪɴ <b><u><code>{get_time(DELETE_TIME)}</code></u> 🫥 <i></b>(ᴅᴜᴇ ᴛᴏ ᴄᴏᴘʏʀɪɢʜᴛ ɪꜱꜱᴜᴇꜱ)</i>.\n\n<b><i>ᴘʟᴇᴀꜱᴇ ꜀ᴏʀᴡᴀʀᴅ ᴛʜɪꜱ ꜀ɪʟᴇ ᴛᴏ ꜱᴏᴍᴇᴡʜᴇʀᴇ ᴇʟꜱᴇ ᴀɴᴅ ꜱᴛᴀʀᴛ ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ ᴛʜᴇʀᴇ</i></b>")
        await asyncio.sleep(DELETE_TIME)
        for x in filesarr:
            await x.delete()
        await k.edit_text("<b>ʏᴏᴜʀ ᴀʟʟ ᴠɪᴅᴇᴏꜱ/꜀ɪʟᴇꜱ ᴀʀᴇ ᴅᴇʟᴇᴛᴇᴅ ꜱᴜᴄᴄᴇꜱꜱ꜀ᴜʟʟʏ !\nᴋɪɴᴅʟʏ ꜱᴇᴀʀᴄʜ ᴀɢᴀɪɴ</b>")
        return
    elif data.startswith("files"):
        current_time = datetime.now(pytz.timezone(TIMEZONE))
        curr_time = current_time.hour        
        if curr_time < 12:
            gtxt = "ɢᴏᴏᴅ ᴍᴏʀɴɪɴɢ  👋" 
        elif curr_time < 17:
            gtxt = "ɢᴏᴏᴅ ᴀғᴛᴇʀɴᴏᴏɴ  👋" 
        elif curr_time < 21:
            gtxt = "ɢᴏᴏᴅ ᴇᴠᴇɴɪɴɢ  👋"
        else:
            gtxt = "ɢᴏᴏᴅ ɴɪɢʜᴛ  👋"     
        user_id = message.from_user.id
        if temp.SHORT.get(user_id)==None:
            return await message.reply_text(text="<b>Please Search Again in Group</b>")
        else:
            chat_id = temp.SHORT.get(user_id)
        settings = await get_settings(chat_id)
        if not await db.has_premium_access(user_id) and settings['is_shortlink']: #Don't change anything without my permission @cosmic_freak
            files_ = await get_file_details(file_id)
            files = files_[0]
            g = await get_shortlink(chat_id, f"https://telegram.me/{temp.U_NAME}?start=file_{file_id}")
            k = await client.send_message(chat_id=message.from_user.id,text=f"🫂 ʜᴇʏ {message.from_user.mention}, {gtxt}\n\n✅ ʏᴏᴜʀ ʟɪɴᴋ ɪꜱ ʀᴇᴀᴅʏ, ᴋɪɴᴅʟʸ ᴄʟɪᴄᴋ ᴏɴ ᴅᴏᴡɴʟᴏᴀᴅ ʙᴜᴛᴛᴏɴ.\n\n⚠️ ꜀ɪʟᴇ ɴᴀᴍᴇ : <code>{files.file_name}</code> \n\n📥 ꜀ɪʟᴇ ꜱɪᴢᴇ : <code>{get_size(files.file_size)}</code>\n\n", reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton('📁 ᴅᴏᴡɴʟᴏᴀᴅ 📁', url=g)
                        ], [
                            InlineKeyboardButton('⚡ ʜᴏᴡ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ ⚡', url=await get_tutorial(chat_id))
                        ]
                    ]
                )
            )
            await asyncio.sleep(600)
            await k.edit("<b>ʏᴏᴜʀ ᴍᴇꜱꜱᴀɢᴇ ɪꜱ ᴅᴇʟᴇᴛᴇᴅ !\nᴋɪɴᴅʟʸ ꜱᴇᴀʀᴄʜ ᴀɢᴀɪɴ.</b>")
            return   
    user = message.from_user.id
    files_ = await get_file_details(file_id)        
    if not files_:
        pre, file_id = ((base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))).decode("ascii")).split("_", 1)
        try:
            if await db.has_premium_access(message.from_user.id): 
                pass 
            else:
               if not await check_verification(client, message.from_user.id) and VERIFY == True:
                   btn = [[
                       InlineKeyboardButton("ᴄʟɪᴄᴋ ʜᴇʀᴇ ᴛᴏ ᴠᴇʀɪғʏ", url=await get_token(client, message.from_user.id, f"https://telegram.me/{temp.U_NAME}?start=", file_id))
                   ],[
                        InlineKeyboardButton("ʜᴏᴡ ᴛᴏ ᴠᴇʀɪғʏ", url=HOW_TO_VERIFY)
                   ]]
                   l = await message.reply_text(
                       text=f"<blockquote><b>ʜᴇʏ ʙʀᴏ,\n\n ‼️ ʏᴏᴜ'ʀᴇ ɴᴏᴛ ᴠᴇʀɪғɪᴇᴅ ᴛᴏᴅᴀʏ ‼️\n\n ›› ᴘʟᴇᴀsᴇ ᴠᴇʀɪғʏ ᴀɴᴅ ɢᴇᴛ ᴜɴʟɪᴍɪᴛᴇᴅ ᴀᴄᴄᴇss ғᴏʀ {VERIFY_EXPIRE} ʜᴏᴜʀs ✅\n\n ›› ɪғ ʏᴏᴜ ᴡᴀɴᴛ ᴅɪʀᴇᴄᴛ ꜀ɪʟᴇs ᴛʜᴇɴ ʏᴏᴜ ᴄᴀɴ ᴛ�.aᴋᴇ ᴘʀᴇᴍɪᴜᴍ sᴇʀᴠɪᴄᴇs.</blockquote></b>",
                       protect_content=False,
                       reply_markup=InlineKeyboardMarkup(btn)
                   )
                   await asyncio.sleep(180)
                   await l.delete()
                   return
            if STREAM_MODE:
                btn = [
                    [InlineKeyboardButton('🚀 ꜀ᴀꜱᴛ ᴅᴏᴡɴʟᴏᴀᴅ / ᴡᴀᴛᴄʜ ᴏɴʟɪɴᴇ 🖥️', callback_data=f'generate_stream_link:{file_id}')],
                    [InlineKeyboardButton('📌 ᴊᴏɪɴ ᴜᴘᴅᴀᴛᴇꜱ ᴄʜ�.aɴɴᴇʟ 📌', url=MOVIE_UPDATE_CHANNEL_LNK)]  # Keep this line unchanged
                ]
            else:
                btn = [
                    [InlineKeyboardButton('📌 ᴊᴏɪɴ ᴜᴘᴅᴀᴛᴇꜱ ᴄʜ�.aɴɴᴇʟ 📌', url=MOVIE_UPDATE_CHANNEL_LNK)]
                ]
            msg = await client.send_cached_media(
                chat_id=message.from_user.id,
                file_id=file_id,
                protect_content=True if pre == 'filep' else False,
                reply_markup=InlineKeyboardMarkup(btn))

            filetype = msg.media
            file = getattr(msg, filetype.value)
            title = ' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@') and not x.startswith('www.'), file.file_name.split()))
            size=get_size(file.file_size)
            f_caption = f"<code>{title}</code>"
            if CUSTOM_FILE_CAPTION:
                try:
                    f_caption=CUSTOM_FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='')
                except:
                    return
            await msg.edit_caption(f_caption)
            btn = [[
                InlineKeyboardButton("❗ ɢᴇᴛ ꜀ɪʟᴇ ᴀɢᴀɪɴ ❗", callback_data=f'delfile#{file_id}')
            ]]
            k = await msg.reply(
                f"<b><u>❗️❗️❗️IMPORTANT❗️️❗️❗️</u></b>\n\n"
                f"ᴛʜɪꜱ ᴍᴏᴠɪᴇ ꜀ɪʟᴇ/ᴠɪᴅᴇᴏ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ ɪɴ <b><u><code>{get_time(DELETE_TIME)}</code></u> 🫥 <i></b>"
                "(ᴅᴜᴇ ᴛᴏ ᴄᴏᴘʏʀɪɢʜᴛ ɪꜱꜱᴜᴇꜱ)</i>.\n\n"
                "<b><i>ᴘʟᴇᴀꜱᴇ ꜀ᴏʀᴡᴀʀᴅ ᴛʜɪꜱ ꜀ɪʟᴇ ᴛᴏ ꜱᴏᴍᴇᴡʜᴇʀᴇ ᴇʟꜱᴇ ᴀɴᴅ ꜱᴛ�.aʀᴛ ᴅᴏᴡɴʟᴏ�.aᴅɪɴɢ ᴛʜᴇʀᴇ</i></b>",
                quote=True
            )
            await asyncio.sleep(DELETE_TIME)
            await msg.delete()
            await k.edit_text("<b>ʏᴏᴜʀ ᴠɪᴅᴇᴏ / ꜀ɪʟᴇ ɪꜱ ꜱᴜᴄᴄᴇꜱꜱ꜀ᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ !!</b>")
            return
        except:
            pass
        return await message.reply('ɴᴏ ꜱᴜᴄʜ ꜀ɪʟᴇ ᴇxɪꜱᴛꜱ !')
    
    files = files_[0]
    title = ' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@') and not x.startswith('www.'), files.file_name.split()))
    size = get_size(files.file_size)
    f_caption = files.caption

    if CUSTOM_FILE_CAPTION:
        try:
            f_caption=CUSTOM_FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)
        except Exception as e:
            logger.exception(e)
            f_caption = f_caption

    if f_caption is None:
        f_caption = ' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@') and not x.startswith('www.'), files.file_name.split()))

    if await db.has_premium_access(message.from_user.id):
        pass
    else:
        if not await check_verification(client, message.from_user.id) and VERIFY == True:
            btn = [[
              InlineKeyboardButton("ᴄʟɪᴄᴋ ʜᴇʀᴇ ᴛᴏ ᴠᴇʀɪғʏ", url=await get_token(client, message.from_user.id, f"https://telegram.me/{temp.U_NAME}?start=", file_id))
           ],[
              InlineKeyboardButton("ʜᴏᴡ ᴛᴏ ᴠᴇʀɪғʏ", url=HOW_TO_VERIFY)
           ]]
            l = await message.reply_text(
                text=f"<blockquote><b>ʜᴇʏ ʙʀᴏ,\n\n ‼️ ʏᴏᴜ'ʀᴇ ɴᴏᴛ ᴠᴇʀɪғɪᴇᴅ ᴛᴏᴅ�.aʏ ‼️\n\n ›› ᴘʟᴇ�.aꜱᴇ ᴠᴇʀɪғʏ ᴀɴᴅ ɢᴇᴛ ᴜɴʟɪᴍɪᴛᴇᴅ ᴀᴄᴄᴇꜱꜱ ғᴏʀ {VERIFY_EXPIRE} ʜᴏᴜʀꜱ ✅\n\n ›› ɪғ ʏᴏᴜ ᴡ�.aɴᴛ ᴅɪʀᴇᴄᴛ ꜀ɪʟᴇꜱ ᴛʜᴇɴ ʏᴏᴜ ᴄ�.aɴ ᴛ�.aᴋᴇ ᴘʀᴇᴍɪᴜᴍ ꜱᴇʀᴠɪᴄᴇꜱ.</blockquote></b>",
                protect_content=False,
                reply_markup=InlineKeyboardMarkup(btn)
            )
            await asyncio.sleep(180)
            await l.delete()
            return
    if STREAM_MODE:
        btn = [
            [InlineKeyboardButton('🚀 ꜀ᴀꜱᴛ ᴅᴏᴡɴʟᴏ�.aᴅ / ᴡ�.aᴛᴄʜ ᴏɴʟɪɴᴇ 🖥️', callback_data=f'generate_stream_link:{file_id}')],
            [InlineKeyboardButton('📌 ᴊᴏɪɴ ᴜᴘᴅ�.aᴛᴇꜱ ᴄʜ�.aɴɴᴇʟ 📌', url=MOVIE_UPDATE_CHANNEL_LNK)]  # Keep this line unchanged
        ]
    else:
        btn = [
            [InlineKeyboardButton('📌 ᴊᴏɪɴ ᴜᴘᴅ�.aᴛᴇꜱ ᴄʜ�.aɴɴᴇʟ 📌', url=MOVIE_UPDATE_CHANNEL_LNK)]
        ]
    msg = await client.send_cached_media(
        chat_id=message.from_user.id,
        file_id=file_id,
        caption=f_caption,
        protect_content=True if pre == 'filep' else False,
        reply_markup=InlineKeyboardMarkup(btn)
    )
    btn = [[
            InlineKeyboardButton("❗ ɢᴇᴛ ꜀ɪʟᴇ ᴀɢ�.aɪɴ ❗", callback_data=f'delfile#{file_id}')
        ]]
    k = await msg.reply(
        f"<b><u>❗️❗️❗️IMPORTANT❗️️❗️❗️</u></b>\n\n"
        f"ᴛʜɪꜱ ᴍᴏᴠɪᴇ ꜀ɪʟᴇ/ᴠɪᴅᴇᴏ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ ɪɴ <b><u><code>{get_time(DELETE_TIME)}</code></u> 🫥 <i></b>"
        "(ᴅᴜᴇ ᴛᴏ ᴄᴏᴘʏʀɪɢʜᴛ ɪꜱꜱᴜᴇꜱ)</i>.\n\n"
        "<b><i>ᴘʟᴇ�.aꜱᴇ ꜀ᴏʀᴡ�.aʀᴅ ᴛʜɪꜱ ꜀ɪʟᴇ ᴛᴏ ꜱᴏᴍᴇᴡʜᴇʀᴇ ᴇʟꜱᴇ �.aɴᴅ ꜱᴛ�.aʀᴛ ᴅᴏᴡɴʟᴏ�.aᴅɪɴɢ ᴛʜᴇʀᴇ</i></b>",
        quote=True
    )     
    await asyncio.sleep(DELETE_TIME)
    await msg.delete()
    await k.edit_text("<b>ʏᴏᴜʀ ᴠɪᴅᴇᴏ / ꜀ɪʟᴇ ɪꜱ ꜱᴜᴄᴄᴇꜱꜱ꜀ᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ !!</b>")
    return
