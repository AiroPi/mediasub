from __future__ import annotations

import pathlib
import typing

import aiosqlite

if typing.TYPE_CHECKING:
    from .source import Identifiable


class Database:
    def __init__(self, path: str):
        self.path = pathlib.Path(path)
        self._connection: aiosqlite.Connection | None = None

    async def connect(self):
        self._connection = await aiosqlite.connect(self.path)

    @property
    def connection(self) -> aiosqlite.Connection:
        if self._connection is None:
            raise RuntimeError("You must fist connect to the database using `await db.connect()`")
        return self._connection

    @property
    def cursor(self):
        return self.connection.cursor

    async def init(self):
        if self._connection is None:
            await self.connect()

        async with self.cursor() as cursor:
            sql = """
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                identifier TEXT
            )
            """
            await cursor.execute(sql)
        await self.connection.commit()

    async def already_processed(self, content: Identifiable) -> bool:
        sql = """SELECT * FROM history WHERE identifier = ?"""
        async with self.cursor() as cursor:
            await cursor.execute(sql, (content.id,))
            return await cursor.fetchone() is not None

    async def add(self, content: Identifiable) -> None:
        sql = """INSERT INTO history (identifier) VALUES (?)"""
        async with self.cursor() as cursor:
            await cursor.execute(sql, (content.id,))
        await self.connection.commit()
