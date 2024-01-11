import asyncio
import logging
import os
import json
import sys
import io
import datetime
import qrcode
import tracemalloc
import websockets
import ws_defs
import typing
import telethon
import telethon.tl.patched
import telethon.tl.types
import telethon.tl.custom.messagebutton
import telethon.tl.functions.messages
from telethon import TelegramClient
from urllib.parse import urlparse, parse_qs


def exit_after_enter():
    sys.stdout.flush()
    input("\nPress enter to exit...\n")
    exit(1)


tracemalloc.start()

NO_COLOR_MODE = os.getenv("NO_COLOR", "").lower() in ("true", "1", "yes")
# logging level for 3rd party libraries
GLOBAL_LOGGING_LEVEL = logging.WARNING
# logging level for the bot
LOCAL_LOGGING_LEVEL = logging.DEBUG
LOGGING_FORMAT = "%(asctime)-15s.%(msecs)03d [%(levelname)-8s] %(name)-22s > %(filename)-18s:%(lineno)-5d - %(message)s"
LOGGING_DT_FORMAT = "%b %d %H:%M:%S"

if not NO_COLOR_MODE:
    import colorlog

    # color handler+formatter
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    formatter = colorlog.ColoredFormatter(
        "%(log_color)s" + LOGGING_FORMAT,
        datefmt=LOGGING_DT_FORMAT,
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        },
    )
    handler.setFormatter(formatter)

    # global logging
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(GLOBAL_LOGGING_LEVEL)

    logging.basicConfig(
        format=LOGGING_FORMAT,
        datefmt=LOGGING_DT_FORMAT,
        level=root_logger.level,
    )

    # local logging
    logger = logging.getLogger(os.path.basename("notcoin").split(".")[0])
    logger.setLevel(LOCAL_LOGGING_LEVEL)
    logger.propagate = False
    logger.addHandler(handler)
else:
    logging.basicConfig(
        format=LOGGING_FORMAT,
        datefmt=LOGGING_DT_FORMAT,
        level=GLOBAL_LOGGING_LEVEL,
    )
    logger = logging.getLogger(os.path.basename("notcoin").split(".")[0])
    logger.setLevel(LOCAL_LOGGING_LEVEL)

if not os.path.isdir("sessions"):
    os.mkdir("sessions")

if not os.path.isfile("configuration.json"):
    logger.error("configuration.json not found")
    exit_after_enter()

with open("configuration.json") as f:
    configuration = json.load(f)

if not os.path.isfile("license.txt"):
    logger.error(
        "license.txt not found. Create `license.txt` and put your license there."
    )
    exit_after_enter()

with open("license.txt") as f:
    license_key = f.read().strip()

del f


class ServerNotRunningException(Exception):
    pass


async def execute_tasks_in_chunks(
    tasks: list,
    chunk_size: int,
) -> list:
    results = []
    for i in range(0, len(tasks), chunk_size):
        results += await asyncio.gather(*tasks[i : i + chunk_size])
    return results


class NotCoinAccountClient:
    def __init__(self, name, config):
        self.name = name
        self.proxy = config["proxy"]
        if not self.proxy:
            logger.error(f"Proxy for account {self.name} not found!")
            exit_after_enter()
        self.configuration = config.get("configuration")
        if self.configuration is None:
            self.configuration = configuration["bot_config"]

        self.telegram_client: typing.Optional[TelegramClient] = None
        self.logger = logger.getChild("accounts").getChild(self.name)

    async def prepare_telegram_client(self):
        if self.telegram_client:
            return
        self.telegram_client = TelegramClient(
            "sessions/" + self.name, **configuration["tg_kwargs"]
        )
        await self.telegram_client.connect()
        if not await self.telegram_client.is_user_authorized():
            self.logger.info(
                f"Telegram client {self.name} is not authorized! Please scan qr code in your telegram app.."
            )
            # await self.telegram_client.start()
            tg_qr = await self.telegram_client.qr_login()
            while True:
                qr = qrcode.QRCode()
                qr.add_data(tg_qr.url)
                qr_f = io.StringIO()
                qr.print_ascii(out=qr_f)
                qr_f.seek(0)
                print(qr_f.read())
                expires_in = tg_qr.expires.timestamp() - datetime.datetime.now().timestamp()
                try:
                    await tg_qr.wait(timeout=expires_in)
                    break
                except asyncio.TimeoutError:
                    self.logger.warning("Qr expired!")
                    await tg_qr.recreate()

            self.logger.info(f"Telegram client {self.name} authorized!")
        else:
            self.logger.info(f"Telegram client {self.name} authorized!")

    async def get_webapp_data(self) -> typing.Tuple[str, str]:
        await self.prepare_telegram_client()
        ent = await self.telegram_client.get_entity("@notcoin_bot")
        input_ent = await self.telegram_client.get_input_entity(ent)

        messages = await self.telegram_client.get_messages(entity=ent)
        if len(messages) == 0:
            message_to_send = "/start"
            if configuration["ref"]:
                message_to_send += " " + configuration["ref"]
            self.logger.info(f"No messages found, sending {message_to_send}")
            await self.telegram_client.send_message(input_ent, message_to_send)

            while True:
                messages = await self.telegram_client.get_messages(entity=ent)
                if len(messages) >= 2:
                    break
                await asyncio.sleep(1)

        resp = None
        for message in messages:
            if resp:
                break
            if not message.buttons:
                continue
            for row in message.buttons:
                if resp:
                    break
                for button in row:
                    button: telethon.tl.custom.messagebutton.MessageButton
                    if isinstance(
                        button.button, telethon.tl.types.KeyboardButtonWebView
                    ):
                        req = telethon.tl.functions.messages.RequestWebViewRequest(
                            peer=input_ent,
                            bot=telethon.tl.types.InputUser(
                                user_id=ent.id,
                                access_hash=ent.access_hash,
                            ),
                            platform="android",
                            from_bot_menu=None,
                            start_param=None,
                            theme_params=telethon.tl.types.DataJSON(
                                '{"accent_text_color":"#ed8abf","bg_color":"#25181f",'
                                '"button_color":"#aa6085","button_text_color":"#ffffff",'
                                '"destructive_text_color":"#ec3942","header_bg_color":"#25181f",'
                                '"hint_color":"#866b79","link_color":"#ee89bf",'
                                '"secondary_bg_color":"#34242b","section_bg_color":"#25181f",'
                                '"section_header_text_color":"#ee89bf","subtitle_text_color":"#866b79",'
                                '"text_color":"#f5f5f5"}'
                            ),
                            reply_to=None,
                            send_as=None,
                            url=button.button.url,
                        )
                        resp = await self.telegram_client(req)
                        break

        if not resp:
            raise ValueError(f"No webview found, account {self.name}")

        webapp_data = parse_qs(urlparse(resp.url).fragment)["tgWebAppData"][0]

        return webapp_data, resp.url

    async def get_client_init_ws_data(self) -> ws_defs.WsMessageDataSendClientsClient:
        web_app_data, web_app_url = await self.get_webapp_data()
        return ws_defs.WsMessageDataSendClientsClient(
            name=self.name,
            proxy=self.proxy,
            web_app_data=web_app_data,
            web_app_url=web_app_url,
            configuration=self.configuration,
        )


WS_URL = "wss://nocoin.aperlaqf.work/client_request"
LOCALE = configuration["locale"]
if LOCALE not in ("en", "ru"):
    logger.error(f"Locale {LOCALE} not found! Possible locales: en, ru")
    logger.error(f"Язык {LOCALE} не найден! Возможные языки: en, ru")
    exit_after_enter()


class WebsocketClient:
    def __init__(self, accounts: typing.List[NotCoinAccountClient]):
        self.logger = logger.getChild("websocket")
        self.accounts = {account.name: account for account in accounts}
        self.write_lock = asyncio.Lock()
        self.ws: typing.Optional[websockets.WebSocketClientProtocol] = None
        self._locales = {}

    async def send_message(
        self,
        message_type: ws_defs.WsMessageTypes,
        data: typing.Optional[ws_defs.SomeWsData],
    ):
        async with self.write_lock:
            await self.ws.send(
                json.dumps(
                    ws_defs.WsMessage(message_type, data).to_json(),
                    separators=(",", ":"),
                )
            )

    async def process_message(self, message: str):
        data = json.loads(message)
        msg = ws_defs.WsMessage.from_json(data)
        if msg.message_type == ws_defs.WsMessageTypes.MT_S_InUse:
            logger.error("There is already a client with this license running!")
            exit_after_enter()
        elif msg.message_type == ws_defs.WsMessageTypes.MT_S_SendClients:
            logger.info("Preparing all clients to be used...")
            tasks = []
            for account in self.accounts.values():
                tasks.append(account.get_client_init_ws_data())

            clients_ready = await execute_tasks_in_chunks(tasks, 5)
            logger.info("All clients prepared! Sending...")
            await self.send_message(
                ws_defs.WsMessageTypes.MT_C_SentClients,
                ws_defs.WsDataSentClients(
                    clients=clients_ready,
                ),
            )
            logger.info("All clients sent!")

        elif msg.message_type == ws_defs.WsMessageTypes.MT_S_ErrorDisconnect:
            logger.error("Error from server: " + msg.data.message)
            raise ValueError("Error: " + msg.data.message)
        elif msg.message_type == ws_defs.WsMessageTypes.MT_S_Print:
            message: ws_defs.WsDataPrint = msg.data
            print(message.color.to_str(message.message))
        elif msg.message_type == ws_defs.WsMessageTypes.MT_S_ReloadClient:
            message: ws_defs.WsDataReloadClient = msg.data
            self.logger.info(
                f"Server requested a refreshed data of client {message.client_name}. Refreshing..."
            )
            account = self.accounts[message.client_name]
            await self.send_message(
                ws_defs.WsMessageTypes.MT_C_ClientReloaded,
                await account.get_client_init_ws_data(),
            )
            self.logger.info(f"Client {message.client_name} refreshed!")

        elif msg.message_type == ws_defs.WsMessageTypes.MT_S_ClientFullyStopped:
            self.logger.error(
                f"Server notified that client {msg.data.client_name} is fully stopped."
            )
        elif msg.message_type == ws_defs.WsMessageTypes.MS_S_Locales:
            message: ws_defs.WsDataLocales = msg.data
            if LOCALE not in message.locales:
                raise ValueError(f"Locale {LOCALE} not found!")
            self._locales = message.locales[LOCALE]
        elif msg.message_type == ws_defs.WsMessageTypes.MT_S_LocaledMessage:
            message: ws_defs.WsDataLocaledMessage = msg.data
            if message.locale_key not in self._locales:
                raise ValueError(f"Locale key {message.locale_key} not found!")
            text = self._locales[message.locale_key]
            if message.formatting:
                text = text.format(*message.formatting)
            print(message.color.to_str(text))

    async def run(self):
        try:
            async with websockets.connect(
                WS_URL + "?license_key=" + license_key,
            ) as self.ws:
                self.ws: websockets.WebSocketClientProtocol
                while True:
                    message = await self.ws.recv()
                    await self.process_message(message)
        except websockets.exceptions.InvalidStatusCode as e:
            if e.status_code == 400:
                logger.error("Invalid or expired license key!")
                logger.error("Неверный или просроченный ключ лицензии!")
                exit_after_enter()
            elif e.status_code == 502:
                raise ServerNotRunningException()
            else:
                raise


async def main():
    accounts = []
    for file in os.listdir("configs"):
        with open("configs/" + file) as cnf_read:
            name = file.split(".")[0]
            if name == "example":
                continue
            accounts.append(NotCoinAccountClient(name, json.load(cnf_read)))

    if len(accounts) == 0:
        logger.error("No accounts found")
        exit_after_enter()

    logger.info("Accounts found: " + ", ".join([account.name for account in accounts]))
    logger.info("Authenticating...")
    for account in accounts:
        await account.prepare_telegram_client()

    logger.info("Authenticated! Running websocket client...")
    client = WebsocketClient(accounts)
    while True:
        try:
            await client.run()
        except KeyboardInterrupt:
            exit(0)
        except websockets.exceptions.ConnectionClosedError:
            logger.error("Connection closed")
        except ServerNotRunningException:
            logger.error("Server is not running")
        except Exception as e:
            logger.exception(e)
            exit_after_enter()

        logger.info("Reconnecting in 5 seconds...")
        await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
