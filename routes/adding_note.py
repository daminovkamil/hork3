import asyncio

from routes.states import *

router = Router(name=__name__)


class AddingMessage(StatesGroup):
    name = State()


@router.message(Command("cancel"), AddingMessage.name)
@router.message(F.text.casefold() == "cancel", AddingMessage.name)
async def cancel_handler(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    if "messages" in data:
        for item in data["messages"]:
            await try_delete_msg(item)
    resource_id = data["resource_id"]
    for user_id, message_id in database.get_messages_with_resource(resource_id):
        await try_bot_edit_msg_text(
            chat_id=user_id,
            message_id=message_id,
            **messages.get_resource(resource_id, user_id, False)
        )
    await state.clear()
    await try_delete_msg(message)


@router.callback_query(messages.AddNote.filter())
async def adding_note(query: CallbackQuery, callback_data: messages.ViewResource, state: FSMContext) -> None:
    await state.set_state(AddingMessage.name)
    resource_id = callback_data.resource_id
    await state.update_data(resource_id=resource_id)
    answer = await query.message.answer("Напишите текст, который хотите добавить")
    await add_message(answer, state)
    author_id = query.from_user.id
    if query.from_user.username is None:
        username = "@Автор"
    else:
        username = "@" + query.from_user.username
    for user_id, message_id in database.get_messages_with_resource(resource_id):
        data = messages.get_resource(resource_id, user_id, False)
        text = data["text"] + "\n\n"
        markup = data["reply_markup"]
        text += md.link(username, f"tg://user?id={author_id}") + " печатает\.\.\."
        await try_bot_edit_msg_text(chat_id=user_id,
                                    message_id=message_id,
                                    text=text,
                                    reply_markup=markup)
    await asyncio.sleep(60 * 3)
    if await state.get_state() is not None:
        for user_id, message_id in database.get_messages_with_resource(resource_id):
            await try_bot_edit_msg_text(
                chat_id=user_id,
                message_id=message_id,
                **messages.get_resource(resource_id, user_id, False)
            )
        await delete_messages(state)
        await state.clear()
        await delete_messages(state)
        await state.clear()


@router.message(AddingMessage.name)
async def finishing_addition(message: Message, state: FSMContext) -> None:
    await add_message(message, state)
    data = await state.get_data()
    resource_id = data["resource_id"]
    user_id = message.from_user.id

    if message.from_user.username is None:
        username = "@Автор"
    else:
        username = "@" + message.from_user.username

    resource = database.Resource(resource_id)
    if message.content_type == "text":
        note = database.Note({
            "type": "text",
            "text": message.md_text,
            "author": md.link(username, f"tg://user?id={user_id}"),
            "created": message.date.timestamp(),
        })
        resource.current.append(note)
        resource.archive.append(note)
        resource.save()
    else:
        pass
    for user_id, message_id in database.get_messages_with_resource(resource_id):
        await try_bot_edit_msg_text(
            chat_id=user_id,
            message_id=message_id,
            **messages.get_resource(resource_id, user_id, False)
        )
    await delete_messages(state)
    await state.clear()
