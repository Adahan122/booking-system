import asyncio
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

from telegram_bot import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    logger.error('BOT_TOKEN not set in environment. Copy .env.example to .env and set BOT_TOKEN.')

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(Command(commands=['start']))
async def cmd_start(message: Message):
    await message.answer(
        'Привет! Я простой бот для управления списком заказов.\n\n'
        'Доступные команды:\n'
        '/register - зарегистрироваться\n'
        '/add <текст> - добавить заказ\n'
        '/list - список ваших заказов\n'
        '/delete <id> - удалить заказ по id\n'
        '/stats - статистика'
    )


@dp.message(Command(commands=['register']))
async def cmd_register(message: Message):
    user = await db.create_user(message.from_user.id, username=message.from_user.username, full_name=message.from_user.full_name)
    if user:
        await message.answer('Вы успешно зарегистрированы ✅')
    else:
        await message.answer('Не удалось зарегистрироваться. Попробуйте снова.')


@dp.message(Command(commands=['add']))
async def cmd_add(message: Message):
    # parse args after command
    text = message.get_args() if hasattr(message, 'get_args') else message.text.partition(' ')[2].strip()
    if not text:
        await message.answer('Использование: /add <текст заказа>')
        return

    # ensure user exists
    user = await db.get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer('Вы не зарегистрированы. Введите /register чтобы зарегистрироваться.')
        return

    order = await db.add_order_for_telegram(message.from_user.id, text)
    if order:
        await message.answer(f'Заказ добавлен (id={order["id"]}) ✅')
    else:
        await message.answer('Ошибка при добавлении заказа.')


@dp.message(Command(commands=['list']))
async def cmd_list(message: Message):
    user = await db.get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer('Вы не зарегистрированы. Введите /register чтобы зарегистрироваться.')
        return

    orders = await db.list_orders_for_telegram(message.from_user.id)
    if not orders:
        await message.answer('У вас пока нет заказов.')
        return

    lines = []
    for o in orders:
        created = o['created_at'][:19].replace('T', ' ')
        lines.append(f"{o['id']}. [{created}] {o['description']}")

    await message.answer('\n'.join(lines))


@dp.message(Command(commands=['delete']))
async def cmd_delete(message: Message):
    arg = message.get_args() if hasattr(message, 'get_args') else message.text.partition(' ')[2].strip()
    if not arg or not arg.isdigit():
        await message.answer('Использование: /delete <id>')
        return
    order_id = int(arg)
    ok = await db.delete_order_for_telegram(message.from_user.id, order_id)
    if ok:
        await message.answer(f'Заказ {order_id} удалён ✅')
    else:
        await message.answer('Невозможно удалить: либо заказа нет, либо он не ваш.')


@dp.message(Command(commands=['stats']))
async def cmd_stats(message: Message):
    stats = await db.stats_for_telegram(message.from_user.id)
    text = f"Всего заказов: {stats['total_orders']}\nВаши заказы: {stats['user_orders']}\n\nПоследние заявки:\n"
    for r in stats['recent']:
        when = r['created_at'][:19].replace('T', ' ')
        text += f"{r['id']}. @{r.get('username') or '—'} {when}: {r['description']}\n"
    await message.answer(text)


async def main():
    await db.init_db()
    try:
        logger.info('Starting bot...')
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(main())
