from routes.states import *

router = Router(name=__name__)


class JoiningResource(StatesGroup):
    invite = State()


@router.message(Command("cancel"))
@router.message(F.text.casefold() == "cancel")
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


@router.callback_query(messages.JoinResource.filter())
async def joining_resource(query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(JoiningResource.invite)
    await state.update_data(query=query)
    answer = await query.message.answer(
        text="Введите ваш инвайт код, чтобы присоединиться к ресурсу"
    )
    await add_message(answer, state)


@router.message(JoiningResource.invite)
async def finishing_joining_resource(message: Message, state: FSMContext) -> None:
    await add_message(message, state)
    invite = message.text
    resource_id = database.resource_with_invite(invite)
    if resource_id is None:
        answer = await message.answer("Нет ресурса с таким инвайт кодом\(\(")
        await add_message(answer, state)
        return
    if resource_id in database.resources_with_user(message.from_user.id):
        answer = await message.answer("Вам и так уже доступен ресурс с таким инвайт кодом")
        await add_message(answer, state)
        return
    resource = database.Resource(resource_id)
    resource.users.append(message.from_user.id)
    resource.save()
    name = database.get_resource_name(resource_id, resource.admin_id)
    if name is not None:
        database.set_resource_name(resource_id, message.from_user.id, name)
    await delete_messages(state)
    data = await state.get_data()
    await state.clear()
    query: CallbackQuery = data["query"]
    await try_edit_msg(query.message, **messages.get_user_resources(message.from_user.id))
