from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from pathlib import Path
from typing import Any

from aiogram import Bot
from aiogram import Dispatcher
from aiogram.filters import Command
from aiogram.filters import CommandObject
from aiogram.types import BotCommand
from aiogram.types import Message


APP_NAME = 'allo-code'
BOT_TOKEN = os.environ['ALLO_TOKEN']


xdg_data_home = os.getenv('XDG_DATA_HOME')
if xdg_data_home:
    DATA_DIR = Path(xdg_data_home) / APP_NAME
else:
    DATA_DIR = Path.home() / '.local' / 'share' / APP_NAME


DATA_FILE = DATA_DIR / 'user_groups.json'
DATA_DIR.mkdir(parents=True, exist_ok=True)

private_commands = [
    BotCommand(command='help', description='Show this help message'),
    BotCommand(
        command='g',
        description='Add/remove a user. Usage: /g [+/-] @username',
    ),
    BotCommand(command='call', description='Mention all users in the group'),
    BotCommand(
        command='list',
        description='Show all users in the mention group',
    ),
]


def load_data() -> dict[str, Any]:
    try:
        with open(DATA_FILE, encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
            return {}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_data(data: dict[str, Any]) -> None:
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)


dp = Dispatcher()
user_groups = load_data()


def g_command(args: str | None, chat_id: str) -> str:
    error_msg = (
        '⚠️ *Invalid format!\n'
        'Use `/g + @username` to add or `/g - @username` to remove.'
    )
    if args is None:
        return error_msg

    pattern = re.compile(r'^[+-] {1,}@?\w+$')
    if not pattern.match(args):
        return error_msg

    cmd, user = args.split()
    user = user.replace('@', '')

    if chat_id not in user_groups:
        user_groups[chat_id] = []

    if cmd == '+':
        if user not in user_groups[chat_id]:
            user_groups[chat_id].append(user)
        resp = f'✅ User @{user} has been added to the mention group.'
    else:
        if user in user_groups[chat_id]:
            user_groups[chat_id].remove(user)
        resp = f'🗑️ User @{user} has been *removed from the mention group.'

    save_data(user_groups)
    return resp


def call_command(chat_id: str) -> str:
    users_to_call = user_groups.get(chat_id)

    if users_to_call:
        mention_string = ' '.join([f'@{user}' for user in users_to_call])
        resp = f'📣 Calling all members!\n\n{mention_string}'
    else:
        resp = (
            'Nobody to call! The group is empty.\n'
            'Add users with `/g + @username`.'
        )
    return resp


def list_command(chat_id: str) -> str:
    group_users = user_groups.get(chat_id)
    if not group_users:
        return (
            'ℹ️ The mention group is empty.  '
            'Add users with `/g + @username`.'
        )

    user_list = '\n'.join(f'{i + 1}. @{user}' for i, user in enumerate(group_users))  # noqa: E501
    return f'👥 Users in the mention group:\n\n{user_list}'


def help_command() -> str:
    commands_text = '\n'.join(
        f'/{cmd.command} - {cmd.description}' for cmd in private_commands
    )
    return f'Available commands:\n\n{commands_text}'


@dp.message(Command('g'))
async def handle_group_management(
        message: Message,
        command: CommandObject,
) -> None:
    chat_id = str(message.chat.id)
    await message.reply(g_command(command.args, chat_id))


@dp.message(Command('call'))
async def handle_call_command(message: Message) -> None:
    chat_id = str(message.chat.id)
    await message.reply(call_command(chat_id))


@dp.message(Command('list'))
async def handle_list_command(message: Message) -> None:
    chat_id = str(message.chat.id)
    await message.reply(list_command(chat_id))


@dp.message(Command('help'))
async def handle_help_command(message: Message) -> None:
    await message.reply(help_command())


async def _main() -> None:
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=BOT_TOKEN)
    await bot.set_my_commands(commands=private_commands)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


def main() -> None:
    asyncio.run(_main())


if __name__ == '__main__':
    main()
