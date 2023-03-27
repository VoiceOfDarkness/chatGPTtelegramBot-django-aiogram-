import io
import logging

import openai
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from pydub import AudioSegment

from bot.models import User


def save_user_data(username, user_text, bot_text):
    user = User.objects.create(username=username, user_text=user_text, bot_text=bot_text)
    user.save()


def save_user_voice(username, file_path, user_text, bot_text):
    with open(file_path, 'rb') as f:
        django_file = File(f)
        user = User.objects.create(username=username, user_voice=django_file, user_text=user_text, bot_text=bot_text)
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
            await message.reply(f"Привет {username}!, я бот с AI, отвечу на все твои вопросы!\nSalam {username}!, mən AI ilə bir botam, butun sualarina cavab verecem!\nHi {username}!, I'm a bot with AI, i will answer all your questions")

        @dp.message_handler(commands=['help'])
        async def send_help(message: types.Message):
            await message.reply('Пиши все на Английском, я понимаю пока что только его')

        @dp.message_handler(content_types=types.ContentTypes.VOICE)
        async def handle_voice_message(message: types.Message):
            # Get the file_id of the voice message
            file_id = message.voice.file_id
            user = message.from_user
            username = user.username
            
            # Download the voice message from Telegram
            file = await bot.download_file_by_id(file_id)
            
            # Convert the OGG file to an AudioSegment
            audio_segment = AudioSegment.from_file(io.BytesIO(file.getvalue()), format="ogg")
            
            # Set the output file name and format
            output_file = f'{username}_voice_message.mp3'
            output_format = "mp3"
            
            await message.reply('Ваш Запрос принят и обрабатывается...')
            
            # Convert the AudioSegment to the output format
            audio_segment.export(output_file, format=output_format)
            audio_file = open(output_file, "rb")
            transcript = openai.Audio.transcribe("whisper-1", audio_file)
            
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=transcript['text'],
                max_tokens=3500,
                temperature=0.7
            )
            await message.reply(response.choices[0].text)
            
            await sync_to_async(save_user_voice)(username, output_file, transcript['text'], response.choices[0].text)
            
            # Send the converted file to the user
            # with open(output_file, 'rb') as f:
            #     await bot.send_audio(message.chat.id, f)

        @dp.message_handler()
        async def chat_handler(message: types.Message):
            username = message.from_user.username
            user_text = message.text
            history = await sync_to_async(get_history)(user_text)
            if history is not None:
                prompt = f"{history.user_text} {user_text}"
            else:
                prompt = user_text
            
            await message.reply('Ваш Запрос принят и обрабатывается...')
            
            try:
                response = openai.Completion.create(
                    engine="text-davinci-003",
                    prompt=prompt,
                    max_tokens=3500,
                    temperature=0.7
                )
                await message.reply(response.choices[0].text)
            except openai.error.InvalidRequestError as e:
                # Handle error related to max_tokens
                await message.reply('Ваш Запрос слишком большой, я не могу обработать его')
                logging.error("Error: %s", e)

            await sync_to_async(save_user_data)(username, user_text, response.choices[0].text)

        logging.basicConfig(level=logging.INFO)
        executor.start_polling(dp, skip_updates=True)
        self.stdout.write(self.style.SUCCESS('Bot is running...'))
