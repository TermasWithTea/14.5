import logging
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from aiogram import Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import asyncio
from crud_functions import get_all_products, add_user, is_included, initiate_db

logging.basicConfig(level=logging.DEBUG)

api = '7843730721:AAHprrD38Ilc5vPwKLQ94bsaCpB-ctCeJ7A'  # Замените на ваш токен
bot = Bot(token=api)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()

# Инициализация базы данных
initiate_db()


class UserState(StatesGroup):
    name = State()
    age = State()
    growth = State()
    weight = State()


class RegistrationState(StatesGroup):
    username = State()
    email = State()
    age = State()


@router.message(Command('start'))
async def start_message(message: types.Message, state: FSMContext):
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [
                types.KeyboardButton(text='Результат'),
                types.KeyboardButton(text='Информация'),
                types.KeyboardButton(text='Купить'),
                types.KeyboardButton(text='Регистрация')
            ]
        ],
        resize_keyboard=True
    )
    await message.answer('Добро Пожаловать в калькулятор калорий! Выберите кнопку:', reply_markup=keyboard)


@router.message(lambda message: message.text.lower() == 'регистрация')
async def sing_up(message: types.Message, state: FSMContext):
    await message.answer("Введите имя пользователя (только латинский алфавит):")
    await state.set_state(RegistrationState.username)


@router.message(RegistrationState.username)
async def set_username(message: types.Message, state: FSMContext):
    username = message.text
    if is_included(username):
        await message.answer("Пользователь существует, введите другое имя.")
    else:
        await state.update_data(username=username)
        await message.answer("Введите свой email:")
        await state.set_state(RegistrationState.email)


@router.message(RegistrationState.email)
async def set_email(message: types.Message, state: FSMContext):
    email = message.text
    await state.update_data(email=email)
    await message.answer("Введите свой возраст:")
    await state.set_state(RegistrationState.age)


@router.message(RegistrationState.age)
async def set_age(message: types.Message, state: FSMContext):
    age = message.text
    data = await state.get_data()

    username = data.get('username')
    email = data.get('email')

    # Добавляем пользователя в базу данных
    add_user(username, email, age)
    await message.answer("Регистрация завершена! Добро пожаловать!")
    await state.clear()


@router.message(lambda message: message.text.lower() == 'результат')
async def main_menu(message: types.Message):
    keyiinline = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Расчитать норму калорий', callback_data='calories')],
            [InlineKeyboardButton(text='Формулы расчета', callback_data='formulas')],
        ]
    )
    await message.answer('Выберите опцию:', reply_markup=keyiinline)


@router.callback_query(lambda call: call.data == 'formulas')
async def get_formulas(call: types.CallbackQuery):
    formula_get = ("Формула Миффлина-Сан Жеора:\n"
                   "BMR = 10 * вес (кг) + 6.25 * рост (см) - 5 * возраст (лет) + 5 (для мужчин)\n"
                   "или\n"
                   "BMR = 10 * вес (кг) + 6.25 * рост (см) - 5 * возраст (лет) - 161 (для женщин)")
    await call.message.answer(formula_get)


@router.callback_query(lambda call: call.data == 'calories')
async def set_age(call: types.CallbackQuery, state: FSMContext):
    await call.message.reply('Введите свой возраст:')
    await state.set_state(UserState.age)


@router.message(UserState.age)
async def set_growth(message: types.Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.reply('Введите свой рост:')
    await state.set_state(UserState.growth)


@router.message(UserState.growth)
async def set_weight(message: types.Message, state: FSMContext):
    await state.update_data(growth=message.text)
    await message.reply('Введите свой вес:')
    await state.set_state(UserState.weight)


@router.message(UserState.weight)
async def set_calories(message: types.Message, state: FSMContext):
    await state.update_data(weight=message.text)
    data = await state.get_data()
    age = int(data.get('age'))
    growth = int(data.get('growth'))
    weight = int(data.get('weight'))
    bmr = 10 * weight + 6.25 * growth - 5 * age + 5
    daily_calories = bmr * 1.2
    await message.answer(f'Ваша норма калорий: {daily_calories:.2f} ккал.')
    await state.clear()


@router.message(lambda message: message.text.lower() == 'купить')
async def get_buying_list(message: types.Message):
    products = get_all_products()

    if not products:
        await message.answer("Нет доступных продуктов.")
        return

    for index, product in enumerate(products):
        title, description, price = product
        photo_path = f'photo/{index + 1}.png'

        # Отправляем фото и информацию о продукте
        await message.answer_photo(
            FSInputFile(photo_path),
            caption=f'Название: {title} | Описание: {description} | Цена: {price}'
        )

    key_inline = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=title, callback_data=f'product_buying_{index}')] for index, (title, _, _) in
            enumerate(products)
        ]
    )
    await message.answer("Выберите продукт для покупки:", reply_markup=key_inline)


@router.callback_query(lambda call: call.data.startswith('product_buying_'))
async def send_confirm_message(call: types.CallbackQuery):
    product_index = int(call.data.split('_')[-1])
    products = get_all_products()

    if 0 <= product_index < len(products):
        title, description, price = products[product_index]
        await call.message.answer(f"Вы успешно приобрели продукт: {title} | Цена: {price} руб.")
    else:
        await call.message.answer("Продукт не найден.")


dp.include_router(router)


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
