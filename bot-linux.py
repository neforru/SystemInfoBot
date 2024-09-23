import os
import json
import socket
import psutil
import platform
import discord
from discord.ext import commands

def get_config_path():
       return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')

def load_config():
    config_path = get_config_path()
    with open(config_path, 'r') as f:
        return json.load(f)

config = load_config()
BOT_TOKEN = config['BOT_TOKEN']
CHANNEL_ID = config['CHANNEL_ID']

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

def get_linux_version():
    try:
        with open('/etc/os-release') as f:
            os_info = dict(line.strip().split('=') for line in f)
            return f"{os_info.get('NAME')} {os_info.get('VERSION_ID')}"
    except FileNotFoundError:
        return "Ошибка получения информации об ОС"

def get_system_info():
    system_info = {
        'Имя компьютера': socket.gethostname(),
        '\n **IP-адрес**': socket.gethostbyname(socket.gethostname()) if socket.gethostname() else 'Ошибка получения IP',
        '\n **ОС**': get_linux_version(),
        '\n **Версия ядра**': platform.release(),
        '\n **Архитектура**': platform.architecture()[0],
        '\n **Процессор**': platform.processor(),
        '\n **Частота ЦП**': "{} MHz".format(psutil.cpu_freq().current) if psutil.cpu_freq() else "Недоступно",
        '\n **Ядер процессора**': psutil.cpu_count(logical=False),
        '\n **Логических процессоров**': psutil.cpu_count(logical=True),
    }

    partitions = psutil.disk_partitions()
    disk_info = []
    for p in partitions:
        try:
            usage = psutil.disk_usage(p.mountpoint)
            disk_info.append(
                "Устройство: {}, Точка монтирования: {}, Использовано: {:.2f} GB из {:.2f} GB".format(
                    p.device, p.mountpoint, usage.used / (1024**3), usage.total / (1024**3))
            )
        except PermissionError:
            disk_info.append(
                "Устройство: {}, Точка монтирования: {} - Ошибка доступа".format(p.device, p.mountpoint)
            )
        except Exception as e:
            disk_info.append(
                "Устройство: {}, Точка монтирования: {} - Ошибка: {}".format(p.device, p.mountpoint, e)
            )

    system_info['Диски'] = "n".join(disk_info)

    try:
        memory = psutil.virtual_memory()
        system_info['ОЗУ'] = "Всего: {:.2f} GB, Использовано: {:.2f} GB, Доступно: {:.2f} GB".format(
            memory.total / (1024**3), memory.used / (1024**3), memory.available / (1024**3))
    except Exception as e:
        system_info['ОЗУ'] = "Ошибка получения информации о памяти: {}".format(e)

    return system_info

def format_system_info(system_info):
    formatted_info = ["{}: {}".format(key, value) for key, value in system_info.items() if key != 'Некоторое_значение']
    return "n".join(formatted_info)

@bot.event
async def on_ready():
    print('Logged in as {}'.format(bot.user.name))
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        system_info = get_system_info()
        formatted_message = format_system_info(system_info)
        message = "**🔧 System Info:**\n{}".format(formatted_message)
        await channel.send(message)
        print("Message sent to Discord.")
    else:
        print("Channel not found.")

bot.run(BOT_TOKEN)
