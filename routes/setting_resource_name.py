from routes.states import *

router = Router(name=__name__)


class SettingName(StatesGroup):
    name = State()


@router.callback_query(messages.SetResourceName.filter())
async def setting_resource_name(query: CallbackQuery, callback_data: messages.ViewResource, state: FSMContext) -> None:
    await state.set_state(SettingName.name)
    await state.update_data(resource_id=callback_data.resource_id, query=query)
    answer = await query.message.answer("Напишите, пожалуйста, какое имя вы хотите установить для этого ресурса")
    await add_message(answer, state)


@router.message(SettingName.name)
async def finishing_setting_name(message: Message, state: FSMContext) -> None:
    await add_message(message, state)
    data = await state.get_data()
    resource_id = data["resource_id"]
    query = data["query"]
    user_id = message.from_user.id
    name = message.text.replace("\n", "  ")
    database.set_resource_name(resource_id, user_id, name)
    await try_edit_msg(query.message, **messages.get_resource(resource_id, user_id))
    await delete_messages(state)
    await state.clear()
