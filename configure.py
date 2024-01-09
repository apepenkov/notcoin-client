import os
import json


def main_en():
    if not os.path.isfile("configuration.json"):
        print("Configuration file not found. Please supply following information:")
        print("Telegram API pair (obtain from https://my.telegram.org/apps):")
        api_id = None
        while api_id is None:
            api_id = input("API ID: ").strip()
            api_id = int(api_id) if api_id.isdigit() else None
            if api_id is None:
                print("API ID must be an digit")
        api_hash = None
        while api_hash is None:
            api_hash = input("API hash: ").strip()
            if not api_hash:
                api_hash = None
                continue
            if len(api_hash) != 32:
                print("API hash must be 32 characters long")
                api_hash = None
                continue

        ref = input("Referral code (press enter to leave blank):")
        if not ref:
            ref = None
        else:
            ref = ref.strip()

        print("Saving configuration...")
        with open("example_configuration.json", "r") as f:
            data = json.load(f)

        data["tg_kwargs"]["api_id"] = api_id
        data["tg_kwargs"]["api_hash"] = api_hash
        data["ref"] = ref
        data["locale"] = "en"

        with open("configuration.json", "w") as f:
            json.dump(data, f, indent=4)
        print("Configuration saved!")

    try:
        import telethon
    except ImportError:
        print("Installing requirements...")
        os.system("pip install -r requirements.txt")

    print("Configuration is loaded and ready to use!")


def main_ru():
    if not os.path.isfile("configuration.json"):
        print("Файл конфигурации не найден. Пожалуйста, укажите следующую информацию:")
        print("Telegram API пара (получить можно на https://my.telegram.org/apps):")
        api_id = None
        while api_id is None:
            api_id = input("API ID: ").strip()
            api_id = int(api_id) if api_id.isdigit() else None
            if api_id is None:
                print("API ID должен быть числом")
        api_hash = None
        while api_hash is None:
            api_hash = input("API hash: ").strip()
            if not api_hash:
                api_hash = None
                continue
            if len(api_hash) != 32:
                print("API hash должен быть длиной 32 символа")
                api_hash = None
                continue

        ref = input("Реферальный код (нажмите enter, чтобы оставить пустым):")
        if not ref:
            ref = None
        else:
            ref = ref.strip()

        print("Сохранение конфигурации...")
        with open("example_configuration.json", "r") as f:
            data = json.load(f)

        data["tg_kwargs"]["api_id"] = api_id
        data["tg_kwargs"]["api_hash"] = api_hash
        data["ref"] = ref
        data["locale"] = "ru"

        with open("configuration.json", "w") as f:
            json.dump(data, f, indent=4)
        print("Конфигурация сохранена!")

    try:
        import telethon
    except ImportError:
        print("Установка зависимостей...")
        os.system("pip install -r requirements.txt")

    print("Конфигурация загружена и готова к использованию!")


if __name__ == "__main__":
    print("Select language:")
    print("1. English")
    print("2. Russian")
    while True:
        lang = input("Select: ")
        if lang == "1":
            main_en()
            break
        elif lang == "2":
            main_ru()
            break
        else:
            print("Invalid input")
