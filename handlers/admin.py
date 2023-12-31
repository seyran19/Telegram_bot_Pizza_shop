from aiogram import types
from aiogram.dispatcher import FSMContext, Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from create_bot import bot
from data_base.sqlite_db import sql_add_command, sql_read2, sql_delete_command
from keyboards.admin_kb import button_case_admin
from Logger import my_log

ID = None


class FSMAdmin(StatesGroup):
    photo = State()
    name = State()
    description = State()
    price = State()


# Получаем ID текущего модератора:
# @dp.message_handler(commands=['moderator'], is_chat_admin=True)
async def make_changes(message: types.Message):
    global ID
    ID = message.from_user.id
    await bot.send_message(message.from_user.id, 'Чего надо Хозяин?', reply_markup=button_case_admin)
    await message.delete()


# Хендлер для начала диалога и загрузки нового пункта меню
# @dp.message_handler(commands='Загрузить', state=None)
async def cm_start(message: types.Message):
    if message.from_user.id == ID:
        await FSMAdmin.photo.set()
        my_log.info('Бот в режиме машины состояний!')
        await message.reply('Загрузите фото')


# Выход из машины состояний
# @dp.message_handler(state="*", commands='отмена')
# @dp.message_handler(Text(equals='отмена', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    if message.from_user.id == ID:
        current_state = await state.get_state()
        if current_state is None:
            return
        await state.finish()
        my_log.info('Бот вышел из машины состояний!')
        await message.reply('Ок')


# Ловим первый ответ и пишем в словарь
# @dp.message_handler(content_types=['photo'], state=FSMAdmin.photo)
async def load_photo(message: types.Message, state: FSMContext):
    if message.from_user.id == ID:
        async with state.proxy() as data:
            data['photo'] = message.photo[0].file_id
        await FSMAdmin.next()
        my_log.info('Первое состояние завершено успешно, переходим к след.')
        await message.reply('Теперь введите название')


# Ловим второй ответ и пишем в словарь
# @dp.message_handler(state=FSMAdmin.name)
async def load_name(message: types.Message, state: FSMContext):
    if message.from_user.id == ID:
        async with state.proxy() as data:
            data['name'] = message.text
        await FSMAdmin.next()
        my_log.info('Второе состояние завершено успешно, переходим к след.')
        await message.reply('Теперь введите описание')


# Ловим третий ответ и пишем в словарь
# @dp.message_handler(state=FSMAdmin.description)
async def load_description(message: types.Message, state: FSMContext):
    if message.from_user.id == ID:
        async with state.proxy() as data:
            data['description'] = message.text
        await FSMAdmin.next()
        my_log.info('Третье состояние завершено успешно, переходим к след.')
        await message.reply('Теперь укажите цену')


# Ловим четвертый ответ и пишем в словарь
# @dp.message_handler(state=FSMAdmin.price)
async def load_price(message: types.Message, state: FSMContext):
    if message.from_user.id == ID:
        async with state.proxy() as data:
            data['price'] = float(message.text)
        await sql_add_command(state)
        await state.finish()
        my_log.info('Бот вышел из машины состояний')


# @dp.callback_query_handler(lambda x: x.data and x.data.start_with('del'))
async def del_callback_run(callback: types.CallbackQuery):
    await sql_delete_command(callback.data.replace('del ', ''))
    await callback.answer(text=f'{callback.data.replace("del ", "")} удалена!', show_alert=True)
    my_log.info(f'{callback.data.replace("del ", "")} удалена!')


# @dp.message_handler(commands='Удалить')
async def delete_item(message: types.Message):
    if message.from_user.id == ID:
        read = await sql_read2()
        for ret in read:
            await bot.send_photo(message.from_user.id, ret[0], f'{ret[1]}\nОписание: {ret[2]}\nЦена: {ret[3]}')
            await bot.send_message(message.from_user.id, text='^^^^', reply_markup=InlineKeyboardMarkup(). \
                                   add(InlineKeyboardButton(f'Удалить{ret[1]}', callback_data=f'del {ret[1]}')))


# Регистрируем хендлеры
def register_handlers_admin(dp: Dispatcher):
    dp.register_message_handler(cm_start, commands=['Загрузить'], state=None)
    dp.register_message_handler(cancel_handler, state="*", commands='отмена')
    dp.register_message_handler(cancel_handler, Text(equals='отмена', ignore_case=True), state="*")
    dp.register_message_handler(load_photo, content_types=['photo'], state=FSMAdmin.photo)
    dp.register_message_handler(load_name, state=FSMAdmin.name)
    dp.register_message_handler(load_description, state=FSMAdmin.description)
    dp.register_message_handler(load_price, state=FSMAdmin.price)
    dp.register_message_handler(make_changes, commands=['moderator'], is_chat_admin=True)
    dp.register_callback_query_handler(del_callback_run, lambda x: 'del' in x.data)
    dp.register_message_handler(delete_item, commands='Удалить')

