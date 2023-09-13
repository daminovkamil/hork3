from __future__ import annotations

import json
from mysql.connector import connect
from config import database_data
from random import choice, randint


def run(*args):
    with connect(**database_data) as connection:
        with connection.cursor() as cursor:
            cursor.execute(*args)
            connection.commit()
            return cursor.lastrowid


def one(*args):
    with connect(**database_data) as connection:
        with connection.cursor() as cursor:
            cursor.execute(*args)
            res: tuple | None = cursor.fetchone()
            if res is not None and len(res) == 1:
                return res[0]
            else:
                return res


def all(*args):
    with connect(**database_data) as connection:
        with connection.cursor() as cursor:
            cursor.execute(*args)
            res = cursor.fetchall()
            if len(res) != 0 and len(res[0]) == 1:
                res = [item[0] for item in res]
            return res


class Note:
    def __init__(self, data: dict):
        self.type = data["type"]
        self.author = data["author"]
        self.created = data["created"]

        if self.type == "file":
            self.file_id = str(data["file_id"])
        else:
            self.text = str(data["text"])

    def to_dict(self) -> dict:
        if self.type == "file":
            data = dict(
                type="file",
                file_id=self.file_id,
                author=self.author,
                created=self.created
            )
        else:
            data = dict(
                type="text",
                text=self.text,
                author=self.author,
                created=self.created
            )
        return data


class Resource:
    def generate_invite(self):
        alf = ""
        for c in range(ord('A'), ord('Z') + 1):
            alf += chr(c)
        for c in range(ord('a'), ord('z') + 1):
            alf += chr(c)
        for c in range(ord('0'), ord('9') + 1):
            alf += chr(c)

        self.invite = ""
        invite_len = randint(20, 30)
        for i in range(invite_len):
            self.invite += choice(alf)

    def __init__(self, resource_id: int):
        self.id = resource_id
        data = one("SELECT data FROM resources WHERE id = %s", (resource_id,))

        if data is not None:
            data = json.loads(data)
        else:
            raise KeyError("There is not resource with such resource_id!")

        if "admin_id" not in data:
            data["admin_id"] = 0

        if "archive" not in data:
            data["archive"] = []

        if "current" not in data:
            data["current"] = []

        if "users" not in data:
            data["users"] = []

        if "invite" not in data:
            self.generate_invite()
        else:
            self.invite = data["invite"]

        self.admin_id = int(data["admin_id"])

        self.archive = []
        for item in data["archive"]:
            self.archive.append(Note(item))

        self.current = []
        for item in data["current"]:
            self.current.append(Note(item))

        self.users = []
        for item in data["users"]:
            self.users.append(int(item))

    def save(self):
        data = dict()

        data["admin_id"] = self.admin_id

        data["users"] = self.users

        data["archive"] = []
        for note in self.archive:
            data["archive"].append(note.to_dict())

        data["current"] = []
        for note in self.current:
            data["current"].append(note.to_dict())

        data["invite"] = self.invite

        run("UPDATE resources SET data = %s WHERE id = %s", (json.dumps(data), self.id))

    def delete(self):
        run("DELETE FROM resources WHERE id = %s", (self.id,))


def create_resource(admin_id: int):
    resource_id = run("INSERT INTO resources (data) VALUES ('{}')")
    resource = Resource(resource_id)
    resource.admin_id = admin_id
    resource.users = [admin_id]
    resource.save()
    return resource


def resources_with_admin(admin_id: int):
    resources = []
    for resource_id in all("SELECT id FROM resources WHERE JSON_EXTRACT(data, '$.admin_id') = %s", (admin_id,)):
        resources.append(resource_id)
    return resources


def resources_with_user(user_id: int):
    resources = []
    for resource_id in all("SELECT id FROM resources WHERE JSON_CONTAINS(JSON_EXTRACT(data, '$.users'), '%s', '$')",
                           (user_id,)):
        resources.append(resource_id)
    return resources


def get_resource_name(resource_id: int, user_id: int):
    name: bytes = one("SELECT name FROM resource_names WHERE resource_id = %s AND user_id = %s", (resource_id, user_id))
    if name is not None:
        return name.decode(encoding='utf8')
    else:
        return None


def set_resource_name(resource_id: int, user_id: int, name: str):
    if get_resource_name(resource_id, user_id) is None:
        values = (resource_id, user_id, name)
        run("INSERT INTO resource_names (resource_id, user_id, name) VALUES (%s, %s, %s)", values)
    else:
        values = (name, resource_id, user_id)
        run("UPDATE resource_names SET name = %s WHERE resource_id = %s AND user_id = %s", values)


def update_resource_message(resource_id: int, user_id: int, message_id):
    old_message_id = one("SELECT message_id FROM resource_messages WHERE user_id = %s", (user_id,))
    if old_message_id == message_id:
        return None
    if old_message_id is None:
        values = (resource_id, user_id, message_id)
        run("INSERT INTO resource_messages (resource_id, user_id, message_id) VALUES (%s, %s, %s)", values)
    else:
        run("UPDATE resource_messages SET message_id = %s WHERE user_id = %s", (message_id, user_id))
    return old_message_id


def get_message_with_user(user_id: int):
    return one("SELECT message_id FROM resource_messages WHERE user_id = %s", (user_id,))


def get_messages_with_resource(resource_id: int):
    return all("SELECT user_id, message_id FROM resource_messages WHERE resource_id = %s", (resource_id,))


def delete_message_with_user(user_id: int):
    return run("DELETE FROM resource_messages WHERE user_id = %s", (user_id,))


def resource_with_invite(invite: str):
    return one("SELECT id FROM resources WHERE JSON_EXTRACT(data, '$.invite') = %s", (invite,))
