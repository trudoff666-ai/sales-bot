import asyncio
import os
import logging
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Update
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_CHAT_ID = os.getenv("OWNER_CHAT_ID")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # https://your-app.onrender.com
WEBHOOK_PATH = "/webhook/sales"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


class LeadForm(StatesGroup):
    name = State()
    business = State()
    problem = State()
    scale = State()
    contact = State()


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💡 Как это работает", callback_data="how_it_works")],
        [InlineKeyboardButton(text="💰 Пакеты и цены", callback_data="pricing")],
        [InlineKeyboardButton(text="🚀 Хочу демо / оставить заявку", callback_data="start_lead")],
    ])


def back_to_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="← Назад в меню", callback_data="menu")],
        [InlineKeyboardButton(text="🚀 Оставить заявку", callback_data="start_lead")],
    ])


@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Привет! 👋\n\n"
        "Я помогаю малому бизнесу перестать терять клиентов из-за медленных ответов.\n\n"
        "Создаю AI-агентов в Telegram, которые:\n"
        "• Отвечают клиентам за 3 секунды — в любое время\n"
        "• Принимают и квалифицируют заявки\n"
        "• Передают горячих лидов менеджеру\n\n"
        "Что хочешь узнать?",
        reply_markup=main_menu()
    )


@dp.callback_query(F.data == "menu")
async def show_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Чем могу помочь?", reply_markup=main_menu())


@dp.callback_query(F.data == "how_it_works")
async def how_it_works(callback: CallbackQuery):
    await callback.message.edit_text(
        "⚙️ <b>Как это работает</b>\n\n"
        "<b>1. Демо (30 мин, бесплатно)</b>\n"
        "Показываю как бот работает на примере вашего бизнеса\n\n"
        "<b>2. Бриф (10 вопросов)</b>\n"
        "Вы рассказываете о своих процессах и клиентах\n\n"
        "<b>3. Разработка (5–30 дней)</b>\n"
        "Настраиваю и тестирую под ваши задачи\n\n"
        "<b>4. Запуск</b>\n"
        "Бот готов, команда обучена — он уже работает на вас\n\n"
        "🔁 После запуска — поддержка и обновления по подписке",
        parse_mode="HTML",
        reply_markup=back_to_menu()
    )


@dp.callback_query(F.data == "pricing")
async def pricing(callback: CallbackQuery):
    await callback.message.edit_text(
        "💰 <b>Пакеты и цены</b>\n\n"
        "🟢 <b>СТАРТ — 49 000 ₽</b>\n"
        "Ответы на вопросы, приём заявок, передача лидов\n"
        "Срок: 5–7 дней\n\n"
        "🔵 <b>БИЗНЕС — 89 000 ₽</b>\n"
        "СТАРТ + квалификация клиента + Google Таблицы\n"
        "Срок: 10–14 дней\n\n"
        "🔴 <b>АВТОПИЛОТ — 150 000 ₽</b>\n"
        "БИЗНЕС + CRM + аналитика + обучение команды\n"
        "Срок: 21–30 дней\n\n"
        "📌 <b>Поддержка:</b> 5 000–12 000 ₽/мес\n\n"
        "Менеджер стоит 45 000 ₽/мес + налоги.\n"
        "Пакет СТАРТ окупается за 5–6 недель.",
        parse_mode="HTML",
        reply_markup=back_to_menu()
    )


@dp.callback_query(F.data == "start_lead")
async def start_lead(callback: CallbackQuery, state: FSMContext):
    await state.set_state(LeadForm.name)
    await callback.message.edit_text(
        "Отлично! Заполним короткую анкету — это займёт 2 минуты.\n\n"
        "Потом я свяжусь с вами лично и покажу демо под ваш бизнес.\n\n"
        "Как вас зовут?"
    )


@dp.message(LeadForm.name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(LeadForm.business)
    await message.answer(f"{message.text.split()[0]}, хорошо!\n\nРасскажите про ваш бизнес — чем занимаетесь, какая сфера?")


@dp.message(LeadForm.business)
async def get_business(message: Message, state: FSMContext):
    await state.update_data(business=message.text)
    await state.set_state(LeadForm.problem)
    await message.answer(
        "Понял.\n\n"
        "Какая главная боль в работе с клиентами прямо сейчас?\n\n"
        "Например: теряем заявки ночью / менеджер перегружен / клиенты долго ждут ответа"
    )


@dp.message(LeadForm.problem)
async def get_problem(message: Message, state: FSMContext):
    await state.update_data(problem=message.text)
    await state.set_state(LeadForm.scale)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="до 20 заявок/мес", callback_data="scale_small")],
        [InlineKeyboardButton(text="20–100 заявок/мес", callback_data="scale_medium")],
        [InlineKeyboardButton(text="100+ заявок/мес", callback_data="scale_large")],
    ])
    await message.answer("Сколько примерно входящих заявок приходит в месяц?", reply_markup=keyboard)


@dp.callback_query(F.data.startswith("scale_"))
async def get_scale(callback: CallbackQuery, state: FSMContext):
    scale_map = {"scale_small": "до 20 заявок/мес", "scale_medium": "20–100 заявок/мес", "scale_large": "100+ заявок/мес"}
    await state.update_data(scale=scale_map[callback.data])
    await state.set_state(LeadForm.contact)
    await callback.message.edit_text("Отлично! Последний вопрос.\n\nУкажите ваш Telegram-username или номер телефона:")


@dp.message(LeadForm.contact)
async def get_contact(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    lead_text = (
        f"🔥 <b>НОВАЯ ЗАЯВКА</b>\n\n"
        f"👤 Имя: {data.get('name')}\n"
        f"🏢 Бизнес: {data.get('business')}\n"
        f"😤 Боль: {data.get('problem')}\n"
        f"📊 Масштаб: {data.get('scale')}\n"
        f"📞 Контакт: {message.text}\n"
        f"🆔 Telegram ID: {message.from_user.id}\n"
        f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )
    await bot.send_message(OWNER_CHAT_ID, lead_text, parse_mode="HTML")
    await message.answer(
        "✅ Заявка принята!\n\n"
        "Свяжусь с вами в течение нескольких часов и покажу демо под ваш бизнес.\n\n"
        "До связи! 👋"
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    await bot.set_webhook(f"{WEBHOOK_URL}{WEBHOOK_PATH}")
    yield
    await bot.delete_webhook()


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post(WEBHOOK_PATH)
async def webhook(request: Request):
    data = await request.json()
    update = Update.model_validate(data)
    await dp.feed_update(bot, update)
    return {"ok": True}
