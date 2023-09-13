from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton
from aiogram.utils.markdown import *
import datetime
import database


class ViewResource(CallbackData, prefix="view_resource"):
    resource_id: int
    full: bool


class DeleteResource(CallbackData, prefix="delete_resource"):
    resource_id: int


class ViewAllResources(CallbackData, prefix="view_all_resources"):
    pass


class ViewResourceArchive(CallbackData, prefix="view_resource_archive"):
    resource_id: int


class ClearNotes(CallbackData, prefix="clear_current_notes"):
    resource_id: int


class AddResource(CallbackData, prefix="add_resource"):
    pass


class JoinResource(CallbackData, prefix="join_resource"):
    pass


class SetResourceName(CallbackData, prefix="set_resource_name"):
    resource_id: int


class AddNote(CallbackData, prefix="add_message"):
    resource_id: int


def get_user_resources(user_id: int):
    resources = database.resources_with_user(user_id)
    if len(resources) == 0:
        text = "Пока у вас нет доступных ресурсов"
    else:
        text = "Вот список доступных ресурсов"
    keyboard = InlineKeyboardBuilder()
    for resource_id in resources:
        name = database.get_resource_name(resource_id, user_id)
        keyboard.button(
            text=f"#{resource_id}" if name is None else name,
            callback_data=ViewResource(resource_id=resource_id, full=False)
        )
    if len(resources) % 3 == 0:
        keyboard.adjust(3)
    elif len(resources) % 3 == 1:
        if len(resources) == 4:
            keyboard.adjust(2, 2)
        else:
            keyboard.adjust(2, 3, 2, 3)
    else:
        keyboard.adjust(3, 2, 3)
    keyboard.row(
        InlineKeyboardButton(text="Создать", callback_data=AddResource().pack()),
        InlineKeyboardButton(text="Присоединиться", callback_data=JoinResource().pack()),
    )
    return dict(text=text, reply_markup=keyboard.as_markup())


def get_resource(resource_id: int, user_id: int, full: bool):
    resource = database.Resource(resource_id)
    info = []
    name = database.get_resource_name(resource_id, user_id)
    if name is not None:
        info.append(code(f"#{resource_id}") + " " + bold(name))
    else:
        info.append(code(f"Ресурс #{resource_id}"))
        info.append(italic("Пока вы никак не назвали этот ресурс"))
    if full:
        info.append(f"Инвайт код для других:\n{code(resource.invite)}")
    for message in resource.current:
        created = datetime.date.fromtimestamp(message.created)
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
        data_string = f"{message.author} {created}"
        if info[-1] == data_string:
            info.pop()
        info.append(f"{message.text}")
        info.append(data_string)
    text = "\n\n".join(info)
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Очистить", callback_data=ClearNotes(resource_id=resource_id))
    keyboard.button(text="Дописать", callback_data=AddNote(resource_id=resource_id))
    keyboard.button(text="Назад", callback_data=ViewAllResources())
    if full:
        keyboard.button(text="Меньше", callback_data=ViewResource(resource_id=resource_id, full=False))
        keyboard.button(
            text="Установить имя" if name is None else "Поменять имя",
            callback_data=SetResourceName(resource_id=resource_id),
        )
        keyboard.button(
            text="Архив записей",
            callback_data=ViewResourceArchive(resource_id=resource_id),
        )
        if resource.admin_id == user_id:
            keyboard.button(
                text="Удалить ресурс",
                callback_data=DeleteResource(
                    resource_id=resource_id,
                )
            )
        else:
            keyboard.button(
                text="Открепить ресурс",
                callback_data=DeleteResource(
                    resource_id=resource_id,
                )
            )
        keyboard.adjust(2, 2, 1, 1)
    else:
        keyboard.button(text="Больше", callback_data=ViewResource(resource_id=resource_id, full=True))
        keyboard.adjust(2)
    return dict(text=text, reply_markup=keyboard.as_markup())
