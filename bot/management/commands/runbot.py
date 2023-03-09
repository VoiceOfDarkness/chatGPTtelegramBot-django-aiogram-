import logging

import openai
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from django.conf import settings
from django.core.management.base import BaseCommand
from bot.models import User
from asgiref.sync import sync_to_async


def save_user_data(username, user_text, bot_text):
    user = User.objects.create(username=username, user_text=user_text, bot_text=bot_text)
    user.save()


def get_history(user_text):
    history = User.objects.filter(user_text=user_text).order_by('-user_text').last()
    return history


class Command(BaseCommand):
    
    help = 'Run Telegram Bot'

    openai.api_key = settings.OPENAI_API_KEY
    
    def handle(self, *args, **options):
        # Initialize bot and dispatcher
        bot_token = settings.TELEGRAM_BOT_TOKEN
        bot = Bot(token=bot_token)
        dp = Dispatcher(bot)
        
        @dp.message_handler(commands=['start'])
        async def start_handler(message: types.Message):
            user = message.from_user
            username = user.username
            await message.reply(f'Привет {username}! Я Слуга "ВСЕВЕЛИКОГО АБИЛЯ" ибад отвечу на все твои вопросы!')

        @dp.message_handler(commands=['help'])
        async def send_help(message: types.Message):
            await message.reply('Пиши все на Английском, я понимаю пока что только его')

        @dp.message_handler()
        async def chat_handler(message: types.Message):
            username = message.from_user.username
            user_text = message.text
            history = await sync_to_async(get_history)(user_text)
            if history is not None:
                prompt = f"{history} {user_text}"
            else:
                prompt = user_text
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=prompt,
                max_tokens=3500
            )
            await message.reply(response.choices[0].text)
    
            await sync_to_async(save_user_data)(username, user_text, response.choices[0].text)

        logging.basicConfig(level=logging.INFO)
        executor.start_polling(dp, skip_updates=True)
        self.stdout.write(self.style.SUCCESS('Bot is running...'))
