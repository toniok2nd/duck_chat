from types import TracebackType
from typing import AsyncGenerator, Self

import aiohttp
import msgspec
from fake_useragent import UserAgent

from .exceptions import (
    ConversationLimitException,
    DuckChatException,
    RatelimitException,
)
from .models import History, ModelType

import json
import os

class DuckChat:
    def __init__(
        self,
        model: ModelType = ModelType.Claude,
        session: aiohttp.ClientSession | None = None,
        user_agent: UserAgent | str = UserAgent(min_version=120.0),
    ) -> None:
        if type(user_agent) is str:
            self.user_agent = user_agent
        else:
            self.user_agent = user_agent.random  # type: ignore

        self._session = session or aiohttp.ClientSession(
            headers={
                "Host": "duckduckgo.com",
                "Accept": "text/event-stream",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Referer": "https://duckduckgo.com/",
                "User-Agent": self.user_agent,
                "x-vqd-4": "",
                "DNT": "1",
                "Sec-GPC": "1",
                "Connection": "keep-alive",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
                "TE": "trailers",
            }
        )
        self.history = History(model, [], "")
        self.vqd = ""
        self.__encoder = msgspec.json.Encoder()
        self.__decoder = msgspec.json.Decoder()

    async def set_history(self, _history):
        self.history = _history

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_value: BaseException | None = None,
        traceback: TracebackType | None = None,
    ) -> None:
        await self._session.__aexit__(exc_type, exc_value, traceback)

    async def load_history(self,_filename='history.json'):
        home_folder = os.path.expanduser('~')
        folder_path=os.path.join(home_folder, '.config','duck_chat')
        fileHistory=os.path.join(folder_path,_filename)
        with open(fileHistory,"r") as f:
            data = f.read()
            data_encode = data.encode('utf-8')
            await self.set_history(msgspec.json.decode(data_encode,type=History))
        self.vqd=self.history.vqd

    async def save_history(self,_filename='history.json'):
        home_folder = os.path.expanduser('~')
        folder_path=os.path.join(home_folder, '.config','duck_chat')
        os.makedirs(folder_path,exist_ok=True)
        fileHistory=os.path.join(folder_path,_filename)
        self.history.vqd=self.vqd
        with open(fileHistory,"w") as f:
            f.write(msgspec.json.encode(self.history).decode('utf-8'))

    async def get_vqd(self) -> None:
        """Get new x-vqd-4 token"""
        async with self._session.get(
            "https://duckduckgo.com/duckchat/v1/status", headers={"x-vqd-accept": "1"}
        ) as response:
            if response.status == 429:
                res = await response.read()
                try:
                    err_message = self.__decoder.decode(res).get("type", "")
                except Exception:
                    raise DuckChatException(res.decode())
                else:
                    raise RatelimitException(err_message)
            if "x-vqd-4" in response.headers:
                self.vqd=response.headers["x-vqd-4"]

    async def get_answer(self) -> str:
        """Get message answer from chatbot"""
        ddata=self.__encoder.encode(self.history.ret_data())

        async with self._session.post(
            "https://duckduckgo.com/duckchat/v1/chat",
            headers={"Content-Type": "application/json",
                "x-vqd-4": self.vqd,
            },
            data=ddata
        ) as response:
            res = await response.read()
            if "x-vqd-4" in response.headers:
                self.vqd=response.headers["x-vqd-4"]
            if response.status == 429:
                raise RatelimitException(res.decode())
            try:
                data = self.__decoder.decode(
                    b"["
                    + b",".join(
                        res.lstrip(b"data: ").rstrip(b"\n\ndata: [DONE][LIMIT_CONVERSATION]\n").split(b"\n\ndata: ")
                    )
                    + b"]"
                )
            except Exception:
                raise DuckChatException(f"Couldn't parse body={res.decode()}")
            message = []
            for x in data:
                if x.get("action") == "error":
                    err_message = x.get("type", "") or str(x)
                    if x.get("status") == 429:
                        if err_message == "ERR_CONVERSATION_LIMIT":
                            raise ConversationLimitException(err_message)
                        raise RatelimitException(err_message)
                    raise DuckChatException(err_message)
                message.append(x.get("message", ""))
        #self.vqd.append(response.headers.get("x-vqd-4", ""))
        return "".join(message)

    async def ask_question(self, query: str) -> str:
        """Get answer from chat AI"""
        self.history.add_input(query)
        message = await self.get_answer()
        self.history.add_answer(message)
        return message

    async def reask_question(self, num: int) -> str:
        """Get re-answer from chat AI"""

        if num >= len(self.vqd):
            num = len(self.vqd) - 1
        self.vqd = self.vqd[:num]

        if not self.history.messages:
            return ""

        if not self.vqd:
            await self.get_vqd()
            self.history.messages = [self.history.messages[0]]
        else:
            num = min(num, len(self.vqd))
            self.history.messages = self.history.messages[: (num * 2 - 1)]
        message = await self.get_answer()
        self.history.add_answer(message)

        return message

