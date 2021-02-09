import logging
import asyncio
import json
import time
from datetime import (date, datetime, timedelta)
import re

from telethon import TelegramClient
import configparser
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import PeerChannel
from telethon import errors


# enable logging
logging.basicConfig(
    filename=f"log {__name__} chipstracker.log",
    format='%(asctime)s - %(funcName)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# get logger
logger = logging.getLogger(__name__)

# get the argument for access from the .config file
config = configparser.ConfigParser()
config.read(".config.ini")


# put each argument in its own variable
api_id = config['Telegram']['api_id']
api_hash = config['Telegram']['api_hash']
phone = config['Telegram']['phone']

# create the TelegramClient that will access ur telegram account using the above arguments
client = TelegramClient(
    "anon",
    api_id,
    api_hash
)


async def main():
    global min_id

    min_id = 50926

    try:
        await client.start()
        logger.info("client started")
        supercoolgroup_channel = await client.get_entity(
            "https://t.me/joinchat/IlXl1EuELwoQ098Vgknn6A"
        )
        captain_supercoolgroup = await client.get_entity("@iGotTimee")
        poker_bot = await client.get_entity("@PokerBot")
        status_abt_cxn = (
            f"got channel -- {supercoolgroup_channel.id}, got captain -- {captain_supercoolgroup.id}, got poker_bot -- {poker_bot.id}"
            )
        logger.info(status_abt_cxn)
    except errors.FloodWaitError as e:
        logger.error(f"Hit the flood-wait-error, Gotta sleep for {e.seconds} seconds")
        time.sleep(e.seconds)
    except errors.FloodError as e:
        logger.error(f"hit a flood error with message -- {e.message}")
        time.sleep(5000)
    except Exception as e:
        logger.exception(f"hit exception -- {e}")
        logger.info("Restarting...")

    while 1:
        try:
            await channel_tracker(
                client,
                supercoolgroup_channel,
                captain_supercoolgroup,
                poker_bot
            )

            time.sleep(600)
            logger.info("looping")
        except errors.FloodWaitError as e:
            logger.error(f"Hit the flood-wait-error, Gotta sleep for {e.seconds} seconds")
            time.sleep(e.seconds)
        except errors.FloodError as e:
            logger.error(f"hit a flood error with message -- {e.message}")
            time.sleep(5000)
        except Exception as e:
            logger.exception(f"hit exception -- {e}")
            logger.info("Restarting script...")
            channel_tracker(client, supercoolgroup_channel, captain_supercoolgroup, poker_bot)


async def channel_tracker(telegram_client, supercoolgroup_channel, captain_supercoolgroup, poker_bot):
    global min_id

    offset_time = datetime.now()

    results = await telegram_client.get_messages(
        entity=supercoolgroup_channel,
        offset_date=offset_time,
        limit=1,
        min_id=min_id,
        search="It's Giveaway Time",
        from_user=captain_supercoolgroup,
    )

    if len(results) != 0:
        logger.info("starting get_giveaway()")
        logger.info(f"the current min_id is {min_id}")
        await scpt2c(telegram_client, poker_bot, supercoolgroup_channel)

        min_id = results[0].id
        msg = results[0].message
        logger.info(f"won the giveaway with id - {min_id} & message {msg}")
    else:
        logger.info("no new giveaway")


async def scpt2c(tlg_client, bot, channel):
    """
    abbrv for send created private table to channel.
    """

    # create the table with all the necessary conditions
    await create_table(tlg_client, bot)

    # sending to the channel
    messages = await tlg_client.inline_query(
        bot=bot,
        query="table",
        entity=channel
    )
    # click & send the private table to the channel
    prv_tbl_btn = messages[0]
    message = await prv_tbl_btn.click(channel, clear_draft=True)

    await call_on_flop(tlg_client, bot)

    return


async def create_table(telegram_client, poker_bot):
    """
    This is a function used to simplify the process of the creating the table.
    """
    # click leave button twice and leave any pre-existing table
    await telegram_client.send_message(entity=poker_bot, message="🏃 Leave")
    time.sleep(0.5)
    await telegram_client.send_message(entity=poker_bot, message="🏃 Leave")

    # click play button and start the process of creating a private table
    await telegram_client.send_message(entity=poker_bot, message="‎🆕 Play")

    time.sleep(0.5)
    messages = await telegram_client.get_messages(poker_bot)
    # search, click & create the private table first
    # crt_prv_tbl_btn = messages[0].buttons[2].pop()
    # await crt_prv_tbl_btn.click()
    await search_and_click("\u200e🔒\xa0Private table", messages)

    messages = await telegram_client.get_messages(poker_bot)
    # search and click the 50k button
    # btn_50k = messages[0].buttons[0][2]
    # btn_50k = messages[0].buttons[0][0]
    # await btn_50k.click()
    await search_and_click("💵\xa0500", messages)

    messages = await telegram_client.get_messages(poker_bot)
    # search and click the No button
    # btn_no = messages[0].buttons[0][0]
    # await btn_no.click()
    await search_and_click("❌ No", messages)

    messages = await telegram_client.get_messages(poker_bot)
    # search and click the 5 players button
    # btn_plyrs_5 = messages[0].buttons[0][0]
    # await btn_plyrs_5.click()
    await search_and_click("5", messages)

    messages = await telegram_client.get_messages(poker_bot)
    # search and click the 30 secs button
    # btn_30sec = messages[0].buttons[0][1]
    # btn_30sec = messages[0].buttons[1][1]
    # await btn_30sec.click()
    await search_and_click("30 seconds", messages)

    logger.info("leaving create_table")


async def call_on_flop(telegram_client, poker_bot):
    """
    This fun calls the first table.
    """
    # if messages contains something that describes that captain has accepted the table, then call_flop
    messages = await telegram_client.get_messages(poker_bot)
    # if re.findall("joined table", messages[0].message, re.IGNORECASE):
    if re.findall("New dealing started!", messages[0].message, re.IGNORECASE):
        # call the flop
        time.sleep(2)
        messages = await telegram_client.get_messages(poker_bot)
        call_flop = messages[0].buttons[0][1]
        await call_flop.click()
        # await search_and_click("\u200e✅\xa250", messages)
        # wait for bot to raise & leave, check to see if you have won is present and then leave
        time.sleep(3)
        messages = await telegram_client.get_messages(bot, search="You have won")
        if re.findall("you have won", messages[0].message):
            await telegram_client.send_message(entity=poker_bot, message="🏃 Leave")
            await telegram_client.send_message(entity=poker_bot, message="🏃 Leave")

            return
    else:
        time.sleep(20)
        await call_on_flop(telegram_client, poker_bot)


async def search_and_click(str_to_search, messages):
    """
    This fun takes the string to search as well as the messages that was retrieved from the bot
    and searches for the str and clicks the button that contains it.
    """
    for message in messages:
        for button in message.buttons:
            for btn in button:
                if btn.text == str_to_search:
                    await btn.click()
                    return


async with client:
    client.loop.run_until_complete(main())
    # client.loop.run_until_complete(channel_tracker())
    # client.loop.run_forever()
