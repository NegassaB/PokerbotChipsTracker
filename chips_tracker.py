import asyncio
import configparser
import json
import logging
import re
import time
from datetime import datetime, timezone

from telethon import TelegramClient, errors
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import PeerChannel

# enable logging
logging.basicConfig(
    # filename=f"log {__name__} chipstracker.log",
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

    min_id = 69736

    async def recall_main():
        logger.info("Restarting...")
        await main()

    try:
        await client.start()
        logger.info("client started")
        supercoolgroup_channel = await client.get_input_entity(
            "https://t.me/joinchat/IlXl1EuELwoQ098Vgknn6A"
        )
        captain_supercoolgroup = await client.get_input_entity("@iGotTimee")
        poker_bot = await client.get_input_entity("@PokerBot")
        status_abt_cxn = (
            f"got channel -- {supercoolgroup_channel.id}, got captain -- {captain_supercoolgroup.id}, got poker_bot -- {poker_bot.id}"
            )
        logger.info(status_abt_cxn)
    except errors.FloodWaitError as e:
        logger.error(f"Hit the flood-wait-error, Gotta sleep for {e.seconds} seconds")
        time.sleep(e.seconds)
        await recall_main()
    except errors.FloodError as e:
        logger.error(f"hit a flood error with message -- {e.message}")
        time.sleep(5000)
        await recall_main()
    except Exception as e:
        logger.exception(f"hit exception -- {e}")
        await recall_main()

    while 1:
        try:
            await channel_tracker(
                client,
                supercoolgroup_channel,
                captain_supercoolgroup,
                poker_bot
            )

            logger.info("looping")
            time.sleep(2)
        except errors.FloodWaitError as e:
            logger.error(
                f"Hit the flood-wait-error, Gotta sleep for {e.seconds} secs"
            )
            time.sleep(e.seconds)
        except errors.FloodError as e:
            logger.error(f"hit a flood error with message -- {e.message}")
            time.sleep(5000)
        except Exception as e:
            logger.exception(f"hit exception -- {e}")
            logger.info("Restarting script...")
            await channel_tracker(
                client,
                supercoolgroup_channel,
                captain_supercoolgroup,
                poker_bot
            )


async def channel_tracker(telegram_client, supercoolgroup_channel, captain_supercoolgroup, poker_bot):
    global min_id

    results = await telegram_client.get_messages(
        entity=supercoolgroup_channel,
        limit=1,
        min_id=min_id,
        search="It's Giveaway Time",
        from_user=captain_supercoolgroup,
    )

    if len(results) != 0:
        logger.info(
            f"starting get_giveaway(), the current min_id is {min_id}, the giveaway min_id is {results[0].id}"
            )
        min_id = results[0].id
        msg = results[0].message

        if await scpt2c(telegram_client, poker_bot, supercoolgroup_channel, captain_supercoolgroup):
            logger.info(
                f"won the giveaway with id - {min_id} & message {msg[0:31]}"
            )
        else:
            logger.info(
                f"COUNLDN'T WIN the giveaway with id - {min_id} & message {msg[0:31]}"
            )
    else:
        logger.info(f"No new giveaway, current min_id is {min_id}")


async def scpt2c(tlg_client, bot, channel, captain_supercoolgroup):
    """
    abbrv for send created private table to channel.
    """

    # create the table with all the necessary conditions
    await create_table(tlg_client, bot)

    # sending to the channel
    messages = await tlg_client.inline_query(
        bot=bot,
        query="table"
    )
    # click & send the private table to the channel
    prv_tbl_btn = messages[0]
    messages = await prv_tbl_btn.click(channel, clear_draft=True)

    time.sleep(7)
    if await call_on_flop(tlg_client, bot, captain_supercoolgroup):
        return True
    else:
        return False


async def create_table(telegram_client, poker_bot):
    """
    This is a function used to simplify the process of the creating the table.
    """
    # click leave button twice and leave any pre-existing table
    await telegram_client.send_message(entity=poker_bot, message="🏃 Leave")
    time.sleep(0.5)
    await telegram_client.send_message(entity=poker_bot, message="🏃 Leave")
    time.sleep(0.5)

    # click play button and start the process of creating a private table
    await telegram_client.send_message(entity=poker_bot, message="‎🆕 Play")

    time.sleep(0.5)
    messages = await telegram_client.get_messages(poker_bot)
    # search, click & create the private table first
    crt_prv_tbl_btn = messages[0].buttons[2].pop()
    await crt_prv_tbl_btn.click()
    # await search_and_click("\u200e🔒\xa0Private table", messages)

    time.sleep(0.5)
    messages = await telegram_client.get_messages(poker_bot)
    # search and click the 50k button
    btn_50k = messages[0].buttons[0][2]
    # btn_50k = messages[0].buttons[0][0]
    await btn_50k.click()
    # await search_and_click("💵\xa0500", messages)

    time.sleep(0.1)
    messages = await telegram_client.get_messages(poker_bot)
    # search and click the No button
    btn_no = messages[0].buttons[0][0]
    await btn_no.click()
    # await search_and_click("❌ No", messages)

    time.sleep(0.5)
    messages = await telegram_client.get_messages(poker_bot)
    # search and click the 5 players button
    btn_plyrs_5 = messages[0].buttons[0][0]
    await btn_plyrs_5.click()
    # await search_and_click("5", messages)

    time.sleep(0.5)
    messages = await telegram_client.get_messages(poker_bot)
    # search and click the 30 secs button
    # btn_30sec = messages[0].buttons[0][1]
    btn_30sec = messages[0].buttons[0][1]
    await btn_30sec.click()
    # await search_and_click("30 seconds", messages)

    logger.info("leaving create_table")


async def call_on_flop(telegram_client, poker_bot, captain_supercoolgroup):
    """
    This fun gets the messages and passes them onto the call() function to actually call the table.
    """
    for _ in range(4):
        # if messages contains something that describes that captain has accepted the table, then call_flop
        messages = await telegram_client.get_messages(poker_bot)
        if "IT IS YOUR TURN" in messages[0].message:
            logger.info(messages[0].message)
            # call the flop
            time.sleep(1)
            call_flop = messages[0].buttons[0][1]
            logger.info(f"about to press the call {call_flop.text}")
            await call_flop.click()
            # await search_and_click("\u200e✅\xa250", messages)
            # # wait for bot to raise & leave, check to see if you have won is present and then leave
            time.sleep(20)
            messages = await telegram_client.get_messages(poker_bot, search="You have won")
            if "👥 Players 1/5" in messages[0].message:
                await telegram_client.send_message(entity=poker_bot, message="🏃 Leave")
                await telegram_client.send_message(entity=poker_bot, message="🏃 Leave")

                return True
        else:
            logger.info("the captain has not accepted the table, sleeping for 5 sec and trying again")
            time.sleep(5)
            continue
    else:
        logger.info("unable to get the giveaway, getting out of call_on_flop")
        await telegram_client.send_message(entity=poker_bot, message="🏃 Leave")
        time.sleep(0.5)
        await telegram_client.send_message(entity=poker_bot, message="🏃 Leave")
        return False


# async def search_and_click(str_to_search, messages):
#     """
#     This fun takes the string to search as well as the messages that was
#     retrieved from the bot and searches for the str and clicks the button
#     that contains it.
#     """
#     for message in messages:
#         for button in message.buttons:
#             for btn in button:
#                 if btn.text == str_to_search:
#                     await btn.click()
#                     return


with client:
    client.loop.run_until_complete(main())
    # client.loop.run_until_complete(channel_tracker())
    # client.loop.run_forever()
