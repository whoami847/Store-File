import asyncio
import random
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot import Bot
from config import *
from helper_func import *
from database.database import *

# Define the list of animated emojis for text message
ANIMATED_EMOJIS = [
    "🔥", "🎉", "💥", "⚡️", "🌟", "⭐", "🎆", "🎇", "🎈", "🎊", "🚀", "💦", "💨"
]

# Sticker file ID
STICKER_ID = "CAACAgUAAxkBAAJFeWd037UWP-vgb_dWo55DCPZS9zJzAAJpEgACqXaJVxBrhzahNnwSHgQ"

@Bot.on_message(filters.command('start') & filters.private & subscribed1 & subscribed2 & subscribed3 & subscribed4)
async def start_command(client: Client, message: Message):
    id = message.from_user.id
    if not await present_user(id):
        try:
            await add_user(id)
        except:
            pass
    text = message.text
    if len(text) > 7:
        try:
            base64_string = text.split(" ", 1)[1]
        except IndexError:
            return
        string = await decode(base64_string)
        argument = string.split("-")
        ids = []
        if len(argument) == 3:
            try:
                start = int(int(argument[1]) / abs(client.db_channel.id))
                end = int(int(argument[2]) / abs(client.db_channel.id))
                ids = range(start, end + 1) if start <= end else list(range(start, end - 1, -1))
            except Exception as e:
                print(f"Error decoding IDs: {e}")
                return
        elif len(argument) == 2:
            try:
                ids = [int(int(argument[1]) / abs(client.db_channel.id))]
            except Exception as e:
                print(f"Error decoding ID: {e}")
                return
        temp_msg = await message.reply("<b>ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ...</b>")
        try:
            messages = await get_messages(client, ids)
        except Exception as e:
            await message.reply_text("sᴏᴍᴇᴛʜɪɴɢ ᴡᴇɴᴛ ᴡʀᴏɴɢ!")
            print(f"Error getting messages: {e}")
            return
        finally:
            await temp_msg.delete()
        codeflix_msgs = []
        for msg in messages:
            caption = (CUSTOM_CAPTION.format(previouscaption="" if not msg.caption else msg.caption.html, 
                                             filename=msg.document.file_name) if bool(CUSTOM_CAPTION) and bool(msg.document)
                       else ("" if not msg.caption else msg.caption.html))
            reply_markup = msg.reply_markup if DISABLE_CHANNEL_BUTTON else None
            try:
                copied_msg = await msg.copy(chat_id=message.from_user.id, caption=caption, parse_mode=ParseMode.HTML, 
                                            reply_markup=reply_markup, protect_content=PROTECT_CONTENT)
                codeflix_msgs.append(copied_msg)
            except FloodWait as e:
                await asyncio.sleep(e.x)
                copied_msg = await msg.copy(chat_id=message.from_user.id, caption=caption, parse_mode=ParseMode.HTML, 
                                            reply_markup=reply_markup, protect_content=PROTECT_CONTENT)
                codeflix_msgs.append(copied_msg)
            except Exception as e:
                print(f"Failed to send message: {e}")
                pass
        if TIME > 0:
            notification_msg = await message.reply(
                f"<b>ᴛʜɪs ꜰɪʟᴇ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ ɪɴ {get_exp_time(TIME)}. ᴘʟᴇᴀsᴇ sᴀᴠᴇ ᴏʀ ꜰᴏʀᴡᴀʀᴅ ɪᴛ ᴛᴏ ʏᴏᴜʀ sᴀᴠᴇᴅ ᴍᴇssᴀɢᴇs ʙᴇꜰᴏʀᴇ ɪᴛ ɢᴇᴛs ᴅᴇʟᴇᴛᴇᴅ.</b>"
            )
            await asyncio.sleep(TIME)
            for snt_msg in codeflix_msgs:
                if snt_msg:
                    try:
                        await snt_msg.delete()
                    except Exception as e:
                        print(f"Error deleting message {snt_msg.id}: {e}")
            try:
                reload_url = (
                    f"https://t.me/{client.username}?start={message.command[1]}"
                    if message.command and len(message.command) > 1
                    else None
                )
                keyboard = InlineKeyboardMarkup(
                    [[InlineKeyboardButton("ɢᴇᴛ ꜰɪʟᴇ ᴀɢᴀɪɴ!", url=reload_url)]]
                ) if reload_url else None
                await notification_msg.edit(
                    "<b>ʏᴏᴜʀ ᴠɪᴅᴇᴏ / ꜰɪʟᴇ ɪs sᴜᴄᴄᴇssꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ !!\n\nᴄʟɪᴄᴋ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴ ᴛᴏ ɢᴇᴛ ʏᴏᴜʀ ᴅᴇʟᴇᴛᴇᴅ ᴠɪᴅᴇᴏ / ꜰɪʟᴇ 👇</b>",
                    reply_markup=keyboard
                )
            except Exception as e:
                print(f"Error updating notification with 'Get File Again' button: {e}")
    else:
        # Send random animated emoji as a formatted text message
        random_emoji = random.choice(ANIMATED_EMOJIS)
        emoji_msg = await message.reply_text(f"<b>{random_emoji}</b>", parse_mode=ParseMode.HTML)
        
        # Wait 1 second and send the sticker
        await asyncio.sleep(1)
        sticker_msg = await message.reply_sticker(sticker=STICKER_ID)
        
        # Wait 1.35 seconds and delete both emoji and sticker
        await asyncio.sleep(1.35)
        try:
            await emoji_msg.delete()
            await sticker_msg.delete()
        except Exception as e:
            print(f"Failed to delete emoji or sticker: {e}")
        
        # Send the standard start message
        reply_markup = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("• ᴍᴏʀᴇ ᴄʜᴀɴɴᴇʟs •", url="https://t.me/MehediYT/50")],
                [InlineKeyboardButton("• ᴀʙᴏᴜᴛ", callback_data="about"),
                 InlineKeyboardButton('ʜᴇʟᴘ •', callback_data="help")]
            ]
        )
        await message.reply_photo(
            photo=START_PIC,
            caption=START_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=None if not message.from_user.username else '@' + message.from_user.username,
                mention=message.from_user.mention,
                id=message.from_user.id
            ),
            reply_markup=reply_markup
        )
        return

@Bot.on_message(filters.command('start') & filters.private)
async def not_joined(client: Client, message: Message):
    buttons = []
    if FORCE_SUB_CHANNEL1 and FORCE_SUB_CHANNEL2:
        buttons.append([
            InlineKeyboardButton(text="• ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ", url=client.invitelink1),
            InlineKeyboardButton(text="ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ •", url=client.invitelink2),
        ])
    elif FORCE_SUB_CHANNEL1:
        buttons.append([
            InlineKeyboardButton(text="• ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ•", url=client.invitelink1)
        ])
    elif FORCE_SUB_CHANNEL2:
        buttons.append([
            InlineKeyboardButton(text="• ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ•", url=client.invitelink2)
        ])
    if FORCE_SUB_CHANNEL3 and FORCE_SUB_CHANNEL4:
        buttons.append([
            InlineKeyboardButton(text="• ᴜɴ ᴄʜᴀɴɴᴇʟ", url=client.invitelink3),
            InlineKeyboardButton(text="ᴜɴ ᴄʜᴀɴɴᴇʟ •", url=client.invitelink4),
        ])
    elif FORCE_SUB_CHANNEL3:
        buttons.append([
            InlineKeyboardButton(text="• ᴜɴ ᴄʜᴀɴɴᴇʟ•", url=client.invitelink3)
        ])
    elif FORCE_SUB_CHANNEL4:
        buttons.append([
            InlineKeyboardButton(text="• ᴜɴ ᴄʜᴀɴɴᴇʟ•", url=client.invitelink4)
        ])
    try:
        buttons.append([
            InlineKeyboardButton(
                text="ʀᴇʟᴏᴀᴅ",
                url=f"https://t.me/{client.username}?start={message.command[1]}"
            )
        ])
    except IndexError:
        pass
    await message.reply_photo(
        photo=FORCE_PIC,
        caption=FORCE_MSG.format(
            first=message.from_user.first_name,
            last=message.from_user.last_name,
            username=None if not message.from_user.username else '@' + message.from_user.username,
            mention=message.from_user.mention,
            id=message.from_user.id
        ),
        reply_markup=InlineKeyboardMarkup(buttons)
    )

WAIT_MSG = "<b>ᴡᴏʀᴋɪɴɢ....</b>"
REPLY_ERROR = "<code>ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ᴀs ᴀ ʀᴇᴘʟʏ ᴛᴏ ᴀɴʏ ᴛᴇʟᴇɢʀᴀᴍ ᴍᴇssᴀɢᴇ ᴡɪᴛʜᴏᴜᴛ ᴀɴʏ sᴘᴀᴄᴇs.</code>"

@Bot.on_message(filters.command('users') & filters.private & filters.user(ADMINS))
async def get_users(client: Bot, message: Message):
    msg = await client.send_message(chat_id=message.chat.id, text=WAIT_MSG)
    users = await full_userbase()
    await msg.edit(f"{len(users)} ᴜsᴇʀs ᴀʀᴇ ᴜsɪɴɢ ᴛʜɪs ʙᴏᴛ")

@Bot.on_message(filters.private & filters.command('broadcast') & filters.user(ADMINS))
async def send_text(client: Bot, message: Message):
    if message.reply_to_message:
        query = await full_userbase()
        broadcast

System: I'm sorry, but it seems your message was cut off. Could you please provide the complete message or clarify what you need help with regarding the `/start` command and animated emojis? 

From our previous conversation, I understand you want to display random animated emojis for the `/start` command in your Telegram bot without using `reply_text`, and you want to maintain the existing flow (sticker after 1 second, delete sticker after 1.35 seconds, then show the start message). You've also indicated that the `set_reaction` method isn't working, likely due to your Pyrogram version or Telegram API limitations.

The last solution I provided included two options:
1. **Using animated GIFs** with `reply_animation` to show animated emoji-like effects.
2. **A fallback using `reply_text`** with animated emojis and formatting for visual appeal.

You asked for alternatives to `reply_text`, and the GIF-based solution was provided, but it requires you to supply valid GIF file IDs. Since you haven't provided GIF IDs or confirmed if you have them, I’ll assume you might need help with that or prefer another approach. Additionally, you mentioned wanting to explore other methods to achieve animated emojis.

### Clarification Needed
To provide the best solution, please clarify:
1. **Do you have access to animated GIF file IDs** or animated sticker IDs? If yes, please share a few so I can update the code.
2. **Do you specifically want animated emojis (e.g., 🔥, 🎉) or are animated stickers/GIFs acceptable** as a replacement for the emoji effect?
3. **Is the `reply_animation` method (for GIFs) acceptable**, or are you looking for something else entirely (e.g., custom emoji stickers, premium emojis)?
4. **Can you share your Pyrogram version**? Run `pip show pyrogram` in your terminal and share the output.
5. **Are you hosting on Koyeb or another platform**, and is there any specific limitation (e.g., Python version, package installation issues)?

### Recommended Solution: Animated Stickers
Based on your requirement to avoid `reply_text` and the fact that `set_reaction` isn’t working, the best alternative is to **use animated stickers** that mimic animated emojis. Animated stickers are visually similar to animated emojis, work with `reply_sticker` (which is reliable across Pyrogram versions), and fit your existing flow. However, you only provided one sticker ID (`CAACAgUAAxkBAAJFeWd037UWP-vgb_dWo55DCPZS9zJzAAJpEgACqXaJVxBrhzahNnwSHgQ`). To implement random animated stickers, you’ll need multiple animated sticker IDs.

If you can provide a list of animated sticker IDs, I’ll update the code to use them. If not, I’ll provide a fallback solution using `reply_text` with enhanced formatting to make the animated emojis more visually appealing, or guide you on how to collect sticker/GIF IDs.

### How to Collect Animated Sticker IDs
1. **Find Animated Stickers**:
   - Search for animated sticker packs in Telegram (e.g., type "animated emojis" in the search bar or use packs like `@AnimatedEmojis`).
   - Add the sticker pack to your Telegram.

2. **Get Sticker IDs**:
   - Send each animated sticker to a chat (e.g., to `@BotFather` or your bot).
   - Use a bot like `@FileIDBot` to get the file ID of each sticker. Forward the sticker to `@FileIDBot`, and it will return the file ID (e.g., `CAACAgIAAxkBAA...`).
   - Collect at least 3–5 animated sticker IDs.

3. **Share the IDs**:
   - Provide the list of sticker IDs to me, and I’ll integrate them into the code.

### Updated Code (Animated Stickers)
Below is the updated `start.py` code assuming you’ll provide multiple animated sticker IDs. I’ve included a placeholder list (`ANIMATED_STICKERS`) that you need to replace with actual IDs. The flow remains the same:
- Send a random animated sticker (instead of an emoji).
- After 1 second, send the provided sticker.
- After 1.35 seconds, delete both stickers.
- Send the standard start message.

<xaiArtifact artifact_id="116c9a6c-ee41-4d05-bcbb-5e34a45319ff" artifact_version_id="85eac915-e3fe-451b-afa6-4b927222bb65" title="start.py (Animated Stickers)" contentType="text/python">
import asyncio
import random
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot import Bot
from config import *
from helper_func import *
from database.database import *

# Define the list of animated sticker file IDs
ANIMATED_STICKERS = [
    "CAACAgUAAxkBAAJFeWd037UWP-vgb_dWo55DCPZS9zJzAAJpEgACqXaJVxBrhzahNnwSHgQ",  # Your provided sticker ID
    # Add more animated sticker IDs here, e.g.:
    # "CAACAgIAAxkBAA...your_sticker_id_2...",
    # "CAACAgIAAxkBAA...your_sticker_id_3..."
]

# Sticker file ID (your original sticker)
STICKER_ID = "CAACAgUAAxkBAAJFeWd037UWP-vgb_dWo55DCPZS9zJzAAJpEgACqXaJVxBrhzahNnwSHgQ"

@Bot.on_message(filters.command('start') & filters.private & subscribed1 & subscribed2 & subscribed3 & subscribed4)
async def start_command(client: Client, message: Message):
    id = message.from_user.id
    if not await present_user(id):
        try:
            await add_user(id)
        except:
            pass
    text = message.text
    if len(text) > 7:
        try:
            base64_string = text.split(" ", 1)[1]
        except IndexError:
            return
        string = await decode(base64_string)
        argument = string.split("-")
        ids = []
        if len(argument) == 3:
            try:
                start = int(int(argument[1]) / abs(client.db_channel.id))
                end = int(int(argument[2]) / abs(client.db_channel.id))
                ids = range(start, end + 1) if start <= end else list(range(start, end - 1, -1))
            except Exception as e:
                print(f"Error decoding IDs: {e}")
                return
        elif len(argument) == 2:
            try:
                ids = [int(int(argument[1]) / abs(client.db_channel.id))]
            except Exception as e:
                print(f"Error decoding ID: {e}")
                return
        temp_msg = await message.reply("<b>ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ...</b>")
        try:
            messages = await get_messages(client, ids)
        except Exception as e:
            await message.reply_text("sᴏᴍᴇᴛʜɪɴɢ ᴡᴇɴᴛ ᴡʀᴏɴɢ!")
            print(f"Error getting messages: {e}")
            return
        finally:
            await temp_msg.delete()
        codeflix_msgs = []
        for msg in messages:
            caption = (CUSTOM_CAPTION.format(previouscaption="" if not msg.caption else msg.caption.html, 
                                             filename=msg.document.file_name) if bool(CUSTOM_CAPTION) and bool(msg.document)
                       else ("" if not msg.caption else msg.caption.html))
            reply_markup = msg.reply_markup if DISABLE_CHANNEL_BUTTON else None
            try:
                copied_msg = await msg.copy(chat_id=message.from_user.id, caption=caption, parse_mode=ParseMode.HTML, 
                                            reply_markup=reply_markup, protect_content=PROTECT_CONTENT)
                codeflix_msgs.append(copied_msg)
            except FloodWait as e:
                await asyncio.sleep(e.x)
                copied_msg = await msg.copy(chat_id=message.from_user.id, caption=caption, parse_mode=ParseMode.HTML, 
                                            reply_markup=reply_markup, protect_content=PROTECT_CONTENT)
                codeflix_msgs.append(copied_msg)
            except Exception as e:
                print(f"Failed to send message: {e}")
                pass
        if TIME > 0:
            notification_msg = await message.reply(
                f"<b>ᴛʜɪs ꜰɪʟᴇ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ ɪɴ {get_exp_time(TIME)}. ᴘʟᴇᴀsᴇ sᴀᴠᴇ ᴏʀ ꜰᴏʀᴡᴀʀᴅ ɪᴛ ᴛᴏ ʏᴏᴜʀ sᴀᴠᴇᴅ ᴍᴇssᴀɢᴇs ʙᴇꜰᴏʀᴇ ɪᴛ ɢᴇᴛs ᴅᴇʟᴇᴛᴇᴅ.</b>"
            )
            await asyncio.sleep(TIME)
            for snt_msg in codeflix_msgs:
                if snt_msg:
                    try:
                        await snt_msg.delete()
                    except Exception as e:
                        print(f"Error deleting message {snt_msg.id}: {e}")
            try:
                reload_url = (
                    f"https://t.me/{client.username}?start={message.command[1]}"
                    if message.command and len(message.command) > 1
                    else None
                )
                keyboard = InlineKeyboardMarkup(
                    [[InlineKeyboardButton("ɢᴇᴛ ꜰɪʟᴇ ᴀɢᴀɪɴ!", url=reload_url)]]
                ) if reload_url else None
                await notification_msg.edit(
                    "<b>ʏᴏᴜʀ ᴠɪᴅᴇᴏ / ꜰɪʟᴇ ɪs sᴜᴄᴄᴇssꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ !!\n\nᴄʟɪᴄᴋ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴ ᴛᴏ ɢᴇᴛ ʏᴏᴜʀ ᴅᴇʟᴇᴛᴇᴅ ᴠɪᴅᴇᴏ / ꜰɪʟᴇ 👇</b>",
                    reply_markup=keyboard
                )
            except Exception as e:
                print(f"Error updating notification with 'Get File Again' button: {e}")
    else:
        # Send random animated sticker
        random_sticker = random.choice(ANIMATED_STICKERS)
        sticker_msg_1 = await message.reply_sticker(sticker=random_sticker)
        
        # Wait 1 second and send the second sticker
        await asyncio.sleep(1)
        sticker_msg_2 = await message.reply_sticker(sticker=STICKER_ID)
        
        # Wait 1.35 seconds and delete both stickers
        await asyncio.sleep(1.35)
        try:
            await sticker_msg_1.delete()
            await sticker_msg_2.delete()
        except Exception as e:
            print(f"Failed to delete stickers: {e}")
        
        # Send the standard start message
        reply_markup = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("• ᴍᴏʀᴇ ᴄʜᴀɴɴᴇʟs •", url="https://t.me/MehediYT/50")],
                [InlineKeyboardButton("• ᴀʙᴏᴜᴛ", callback_data="about"),
                 InlineKeyboardButton('ʜᴇʟᴘ •', callback_data="help")]
            ]
        )
        await message.reply_photo(
            photo=START_PIC,
            caption=START_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=None if not message.from_user.username else '@' + message.from_user.username,
                mention=message.from_user.mention,
                id=message.from_user.id
            ),
            reply_markup=reply_markup
        )
        return

@Bot.on_message(filters.command('start') & filters.private)
async def not_joined(client: Client, message: Message):
    buttons = []
    if FORCE_SUB_CHANNEL1 and FORCE_SUB_CHANNEL2:
        buttons.append([
            InlineKeyboardButton(text="• ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ", url=client.invitelink1),
            InlineKeyboardButton(text="ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ •", url=client.invitelink2),
        ])
    elif FORCE_SUB_CHANNEL1:
        buttons.append([
            InlineKeyboardButton(text="• ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ•", url=client.invitelink1)
        ])
    elif FORCE_SUB_CHANNEL2:
        buttons.append([
            InlineKeyboardButton(text="• ᴜɴ ᴄʜᴀɴɴᴇʟ•", url=client.invitelink2)
        ])
    if FORCE_SUB_CHANNEL3 and FORCE_SUB_CHANNEL4:
        buttons.append([
            InlineKeyboardButton(text="• ᴜɴ ᴄʜᴀɴɴᴇʟ", url=client.invitelink3),
            InlineKeyboardButton(text="ᴜɴ ᴄʜᴀɴɴᴇʟ •", url=client.invitelink4),
        ])
    elif FORCE_SUB_CHANNEL3:
        buttons.append([
            InlineKeyboardButton(text="• ᴜɴ ᴄʜᴀɴɴᴇʟ•", url=client.invitelink3)
        ])
    elif FORCE_SUB_CHANNEL4:
        buttons.append([
            InlineKeyboardButton(text="• ᴜɴ ᴄʜᴀɴɴᴇʟ•", url=client.invitelink4)
        ])
    try:
        buttons.append([
            InlineKeyboardButton(
                text="ʀᴇʟᴏᴀᴅ",
                url=f"https://t.me/{client.username}?start={message.command[1]}"
            )
        ])
    except IndexError:
        pass
    await message.reply_photo(
        photo=FORCE_PIC,
        caption=FORCE_MSG.format(
            first=message.from_user.first_name,
            last=message.from_user.last_name,
            username=None if not message.from_user.username else '@' + message.from_user.username,
            mention=message.from_user.mention,
            id=message.from_user.id
        ),
        reply_markup=InlineKeyboardMarkup(buttons)
    )

WAIT_MSG = "<b>ᴡᴏʀᴋɪɴɢ....</b>"
REPLY_ERROR = "<code>ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ᴀs ᴀ ʀᴇᴘʟʏ ᴛᴏ ᴀɴʏ ᴛᴇʟᴇɢʀᴀᴍ ᴍᴇssᴀɢᴇ ᴡɪᴛʜᴏᴜᴛ ᴀɴʏ sᴘᴀᴄᴇs.</code>"

@Bot.on_message(filters.command('users') & filters.private & filters.user(ADMINS))
async def get_users(client: Bot, message: Message):
    msg = await client.send_message(chat_id=message.chat.id, text=WAIT_MSG)
    users = await full_userbase()
    await msg.edit(f"{len(users)} ᴜsᴇʀs ᴀʀᴇ ᴜsɪɴɢ ᴛʜɪs ʙᴏᴛ")

@Bot.on_message(filters.private & filters.command('broadcast') & filters.user(ADMINS))
async def send_text(client: Bot, message: Message):
    if message.reply_to_message:
        query = await full_userbase()
        broadcast_msg = message.reply_to_message
        total = 0
        successful = 0
        blocked = 0
        deleted = 0
        unsuccessful = 0
        pls_wait = await message.reply("<i>ʙʀᴏᴀᴅᴄᴀsᴛ ᴘʀᴏᴄᴇssɪɴɢ....</i>")
        for chat_id in query:
            try:
                await broadcast_msg.copy(chat_id)
                successful += 1
            except FloodWait as e:
                await asyncio.sleep(e.x)
                await broadcast_msg.copy(chat_id)
                successful += 1
            except UserIsBlocked:
                await del_user(chat_id)
                blocked += 1
            except InputUserDeactivated:
                await del_user(chat_id)
                deleted += 1
            except:
                unsuccessful += 1
                pass
            total += 1
        status = f"""<b><u>ʙʀᴏᴀᴅᴄᴀsᴛ...</u>ᴛᴏᴛᴀʟ ᴜsᴇʀs: <code>{total}</code>sᴜᴄᴄᴇssꜰᴜʟ: <code>{successful}</code>ʙʟᴏᴄᴋᴇᴅ ᴜsᴇʀs: <code>{blocked}</code>ᴅᴇʟᴇᴛᴇᴅ ᴀᴄᴄᴏᴜɴᴛs: <code>{deleted}</code>ᴜɴsᴜᴄᴄᴇssꜰᴜʟ: <code>{unsuccessful}</code></b>"""
        return await pls_wait.edit(status)
    else:
        msg = await message.reply(REPLY_ERROR)
        await asyncio.sleep(8)
        await msg.delete()

@Bot.on_message(filters.private & filters.command('dbroadcast') & filters.user(ADMINS))
async def delete_broadcast(client: Bot, message: Message):
    if message.reply_to_message:
        try:
            duration = int(message.command[1])
        except (IndexError, ValueError):
            await message.reply("<b>ᴘʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴠᴀʟɪᴅ ᴅᴜʀᴀᴛɪᴏɴ ɪɴ sᴇᴄᴏɴᴅs.</b> ᴜsᴀɢᴇ: /dbroadcast {duration}")
            return
        query = await full_userbase()
        broadcast_msg = message.reply_to_message
        total = 0
        successful = 0
        blocked = 0
        deleted = 0
        unsuccessful = 0
        pls_wait = await message.reply("<i>ʙʀᴏᴀᴅᴄᴀsᴛ ᴡɪᴛʜ ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛᴇ ᴘʀᴏᴄᴇssɪɴɢ....</i>")
        for chat_id in query:
            try:
                sent_msg = await broadcast_msg.copy(chat_id)
                await asyncio.sleep(duration)
                await sent_msg.delete()
                successful += 1
            except FloodWait as e:
                await asyncio.sleep(e.x)
                sent_msg = await broadcast_msg.copy(chat_id)
                await asyncio.sleep(duration)
                await sent_msg.delete()
                successful += 1
            except UserIsBlocked:
                await del_user(chat_id)
                blocked += 1
            except InputUserDeactivated:
                await del_user(chat_id)
                deleted += 1
            except:
                unsuccessful += 1
                pass
            total += 1
        status = f"""<b><u>ʙʀᴏᴀᴅᴄᴀsᴛ ᴡɪᴛʜ ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛᴇ...</u>ᴛᴏᴛᴀʟ ᴜsᴇʀs: <code>{total}</code>sᴜᴄᴄᴇssꜰᴜʟ: <code>{successful}</code>ʙʟᴏᴄᴋᴇᴅ ᴜsᴇʀs: <code>{blocked}</code>ᴅᴇʟᴇᴛᴇᴅ ᴀᴄᴄᴏᴜɴᴛs: <code>{deleted}</code>ᴜɴsᴜᴄᴄᴇssꜰᴜʟ: <code>{unsuccessful}</code></b>"""
        return await pls_wait.edit(status)
    else:
        msg = await message.reply("ᴘʟᴇᴀsᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ʙʀᴏᴀᴅᴄᴀsᴛ ɪᴛ ᴡɪᴛʜ ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛᴇ.")
        await asyncio.sleep(8)
        await msg.delete()
