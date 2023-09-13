import asyncio
import sys

from aiogram import Dispatcher
from aiogram.filters import Command
from aiogram.types import ErrorEvent

import routes.joining_resource
import routes.setting_resource_name
import routes.adding_note
import datetime
from routes.states import *

dp = Dispatcher()
dp.include_router(routes.joining_resource.router)
dp.include_router(routes.setting_resource_name.router)
dp.include_router(routes.adding_note.router)


@dp.error(F.update.message.as_("message"))
async def error_handler(event: ErrorEvent, message: Message):
    logging.critical("Critical error caused by %s", event.exception, exc_info=True)
    await message.answer("Возникла ошибка\(\( Обратитесь, пожалуйста, к разработчику")


@dp.error(F.update.callback_query.as_("query"))
async def error_handler(event: ErrorEvent, query: CallbackQuery):
    logging.critical("Critical error caused by %s", event.exception, exc_info=True)
    await query.answer("Возникла ошибка(( Обратитесь, пожалуйста, к разработчику")


@dp.message(Command("cancel"))
@dp.message(F.text.casefold() == "cancel")
async def cancel_handler(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        return
    data = await state.get_data()
    if "messages" in data:
        for item in data["messages"]:
            await try_delete_msg(item)
    await state.clear()
    await try_delete_msg(message)


@dp.callback_query(messages.AddResource.filter())
async def adding_resource(query: CallbackQuery) -> None:
    resource = database.create_resource(query.from_user.id)
    await try_edit_msg(query.message, **messages.get_user_resources(query.from_user.id))
    await query.answer(f"Создан ресурс #{resource.id}")


@dp.message(Command('all'))
async def cmd_all_showing_resources(message: Message) -> None:
    await message.answer(**messages.get_user_resources(message.from_user.id))


@dp.callback_query(messages.ViewAllResources.filter())
async def showing_resources(query: CallbackQuery) -> None:
    message_id = database.get_message_with_user(query.from_user.id)
    if message_id == query.message.message_id:
        database.delete_message_with_user(query.from_user.id)
    await try_edit_msg(query.message, **messages.get_user_resources(query.from_user.id))


@dp.callback_query(messages.ViewResource.filter())
async def showing_resource(query: CallbackQuery, callback_data: messages.ViewResource) -> None:
    message_id = database.update_resource_message(
        resource_id=callback_data.resource_id,
        user_id=query.from_user.id,
        message_id=query.message.message_id
    )
    await try_bot_edit_msg_markup(chat_id=query.from_user.id, message_id=message_id)
    await try_edit_msg(query.message, **messages.get_resource(
        resource_id=callback_data.resource_id,
        user_id=query.from_user.id,
        full=callback_data.full
    ))


@dp.callback_query(messages.ClearNotes.filter())
async def clearing_notes(query: CallbackQuery, callback_data: messages.AddNote) -> None:
    resource = database.Resource(resource_id=callback_data.resource_id)
    resource.current = []
    resource.save()
    await try_edit_msg(query.message, **messages.get_resource(
        resource_id=callback_data.resource_id,
        user_id=query.from_user.id,
        full=False
    ))


@dp.callback_query(messages.ViewResourceArchive.filter())
async def viewing_archive(query: CallbackQuery, callback_data: messages.ViewResourceArchive) -> None:
    resource = database.Resource(callback_data.resource_id)
    for note in resource.archive[-15:]:
        created = datetime.date.fromtimestamp(note.created)
        weekdays = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        months = [
            "Января",
            "Февраля",
            "Марта",
            "Апреля",
            "Мая",
            "Июня",
            "Июля",
            "Августа",
            "Сентября",
            "Октября",
            "Ноября",
            "Декабря"
        ]
        created = f"{weekdays[created.weekday()]}, {created.day} {months[created.month]}"
        data_string = f"{note.author} {created}"
        await query.message.answer(note.text + "\n\n" + data_string)


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
