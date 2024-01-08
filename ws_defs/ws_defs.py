import abc
import enum
import typing


class WsMessageTypes(enum.IntEnum):
    """Enum for WebSocket message types."""

    MT_S_InUse = 0  # this client is already using the server
    MT_S_SendClients = 1  # request to send all clients to be used
    MT_C_SentClients = 2  # response to send all clients to be used
    MT_S_ErrorDisconnect = 3  # error and disconnect
    MT_S_Print = 4  # print to client's console
    MT_S_ReloadClient = 5  # reload client
    MT_C_ClientReloaded = 6  # client reloaded
    MT_S_ClientFullyStopped = 7  # client fully stopped
    MT_C_ActivateTurboBoost = 8  # activate turbo boost


colors = {"green": "\033[92m", "red": "\033[91m", "blue": "\033[94m", "": "\033[0m"}
color_reset = "\033[0m"


class Color(enum.StrEnum):
    Green = "green"
    Red = "red"
    Blue = "blue"
    None_ = ""

    def to_str(self, text: str):
        return color_reset + colors[self.value] + text + color_reset


class SomeWsData(abc.ABC):
    @abc.abstractmethod
    def to_json(self):
        return None

    @classmethod
    @abc.abstractmethod
    def from_json(cls, data):
        return None


class WsMessageDataSendClientsClient(SomeWsData):
    name: str
    proxy: str
    web_app_data: str
    web_app_url: str
    configuration: typing.Optional[dict]

    def __init__(
        self,
        name: str,
        proxy: str,
        web_app_data: str,
        web_app_url: str,
        configuration: typing.Optional[dict] = None,
    ):
        self.name = name
        self.proxy = proxy
        self.web_app_data = web_app_data
        self.web_app_url = web_app_url
        self.configuration = configuration

    def to_json(self):
        res = {
            "name": self.name,
            "proxy": self.proxy,
            "web_app_data": self.web_app_data,
            "web_app_url": self.web_app_url,
        }
        if self.configuration:
            res["configuration"] = self.configuration
        return res

    @classmethod
    def from_json(cls, data):
        return cls(
            name=data["name"],
            proxy=data["proxy"],
            web_app_data=data["web_app_data"],
            web_app_url=data["web_app_url"],
            configuration=data.get("configuration"),
        )


class WsDataErrorDisconnect(SomeWsData):
    message: str

    def __init__(self, message: str):
        self.message = message

    def to_json(self):
        return {"message": self.message}

    @classmethod
    def from_json(cls, data):
        return cls(message=data["message"])


class WsDataPrint(SomeWsData):
    message: str
    color: Color

    def __init__(self, message: str, color: Color):
        self.message = message
        self.color = color

    def to_json(self):
        return {"message": self.message, "color": self.color.value}

    @classmethod
    def from_json(cls, data):
        return cls(message=data["message"], color=Color(data["color"]))


class WsDataSentClients(SomeWsData):
    clients: typing.List[WsMessageDataSendClientsClient]

    def __init__(self, clients: typing.List[WsMessageDataSendClientsClient]):
        self.clients = clients

    def to_json(self):
        return {"clients": [c.to_json() for c in self.clients]}

    @classmethod
    def from_json(cls, data):
        return cls(
            clients=[
                WsMessageDataSendClientsClient.from_json(c) for c in data["clients"]
            ]
        )


class WsDataReloadClient(SomeWsData):
    client_name: str

    def __init__(self, client_name: str):
        self.client_name = client_name

    def to_json(self):
        return {"client_name": self.client_name}

    @classmethod
    def from_json(cls, data):
        return cls(client_name=data["client_name"])


class WsDataClientFullyStopped(SomeWsData):
    client_name: str

    def __init__(self, client_name: str):
        self.client_name = client_name

    def to_json(self):
        return {"client_name": self.client_name}

    @classmethod
    def from_json(cls, data):
        return cls(client_name=data["client_name"])


class WsDataActivateTurboBoost(SomeWsData):
    client_name: str

    def __init__(self, client_name: str):
        self.client_name = client_name

    def to_json(self):
        return {"client_name": self.client_name}

    @classmethod
    def from_json(cls, data):
        return cls(client_name=data["client_name"])


binds = {
    WsMessageTypes.MT_S_InUse: None,
    WsMessageTypes.MT_S_SendClients: None,
    WsMessageTypes.MT_C_SentClients: WsDataSentClients,
    WsMessageTypes.MT_S_ErrorDisconnect: WsDataErrorDisconnect,
    WsMessageTypes.MT_S_Print: WsDataPrint,
    WsMessageTypes.MT_S_ReloadClient: WsDataReloadClient,
    WsMessageTypes.MT_C_ClientReloaded: None,
    WsMessageTypes.MT_S_ClientFullyStopped: WsDataClientFullyStopped,
    WsMessageTypes.MT_C_ActivateTurboBoost: WsDataActivateTurboBoost,
}


class WsMessage:
    message_type: WsMessageTypes
    data: typing.Optional[SomeWsData]

    def __init__(self, message_type: WsMessageTypes, data: SomeWsData):
        self.message_type = message_type
        self.data = data

    def to_json(self):
        return {
            "type": self.message_type,
            "data": (self.data.to_json() if self.data else None),
        }

    @classmethod
    def from_json(cls, data):
        if not isinstance(data, dict):
            raise TypeError("data must be a dict")

        if "type" not in data:
            raise ValueError("data must contain message_type")

        if data["type"] not in binds:
            raise ValueError(
                f"data must contain valid message_type (got {data['type']})"
            )

        data_some_ws_data = binds[data["type"]]
        data_init = (
            data_some_ws_data.from_json(data["data"]) if data_some_ws_data else None
        )
        return cls(
            message_type=WsMessageTypes(data["type"]),
            data=data_init,
        )
