import os
import json
import socket
import psutil
import platform
import winreg
import discord
from discord.ext import commands

def get_config_path():
    return os.path.join(os.path.dirname(__file__), 'config.json')

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

def get_windows_version():
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
        product_name = winreg.QueryValueEx(key, "ProductName")[0]
        release_id = winreg.QueryValueEx(key, "ReleaseId")[0]
        build_number = winreg.QueryValueEx(key, "CurrentBuildNumber")[0]
        return "{} (Build {}, Version {})".format(product_name, build_number, release_id)
    except Exception as e:
        return "Ошибка ОС: {}".format(e)

def get_system_info():
    system_info = {
        'Имя компьютера': os.getenv('COMPUTERNAME', 'Неизвестно'),
        'IP-адрес': socket.gethostbyname(socket.gethostname()) if socket.gethostname() else 'Ошибка получения IP',
        
        'ОС': get_windows_version(),
        'Версия ОС': platform.version(),
        
        'Архитектура': platform.architecture()[0],
        'Процессор': platform.processor(),
        'Частота ЦП': "{} MHz".format(psutil.cpu_freq().current) if psutil.cpu_freq() else "Недоступно",
        'Ядер процессора': psutil.cpu_count(logical=False),
        'Логических процессоров': psutil.cpu_count(logical=True),
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

    system_info['Диски'] = "\n".join(disk_info)

    try:
        memory = psutil.virtual_memory()
        system_info['ОЗУ'] = "Всего: {:.2f} GB, Использовано: {:.2f} GB, Доступно: {:.2f} GB".format(
            memory.total / (1024**3), memory.used / (1024**3), memory.available / (1024**3))
    except Exception as e:
        system_info['ОЗУ'] = "Ошибка получения информации о памяти: {}".format(e)

    return system_info

def format_system_info(system_info):
    formatted_info = ["**{}:** {}".format(key, value) for key, value in system_info.items() if key != 'Некоторое_значение']
    return "\n".join(formatted_info)

@bot.event
async def on_ready():
    print('Logged in as {}'.format(bot.user.name))
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        system_info = get_system_info()
        formatted_message = format_system_info(system_info)
        message = "🔧 **System Info**:\n{}".format(formatted_message)
        await channel.send(message)
        print("Message sent to Discord.")
    else:
        print("Channel not found.")

bot.run(BOT_TOKEN)
