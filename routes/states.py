from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
import aiogram.utils.markdown as md
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram import Bot, Router, F
from asyncio import sleep
import messages
import logging
import database
import config

bot = Bot(config.bot_token, parse_mode=ParseMode.MARKDOWN_V2, disable_web_page_preview=True)


async def try_edit_msg(message: Message, *args, **kwargs):
    try:
        await message.edit_text(*args, **kwargs)
    except Exception as error:
        logging.debug(error)


async def try_delete_msg(message: Message):
    try:
        await message.delete()
    except Exception as error:
        logging.debug(error)


async def try_bot_edit_msg_text(*args, **kwargs):
    try:
        await bot.edit_message_text(*args, **kwargs)
    except Exception as error:
        logging.debug(error)


async def try_bot_edit_msg_markup(*args, **kwargs):
    try:
        await bot.edit_message_reply_markup(*args, **kwargs)
    except Exception as error:
        logging.debug(error)


async def add_message(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        return
    data = await state.get_data()
    if "messages" not in data:
        data["messages"] = []
    data["messages"].append(message)
    await state.set_data(data)


async def delete_messages(state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        return
    data = await state.get_data()
    if "messages" in data:
        for message in data["messages"]:
            await try_delete_msg(message)
