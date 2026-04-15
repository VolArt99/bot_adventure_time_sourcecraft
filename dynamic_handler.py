"""Cloud Functions entrypoint wrapper.

This module stays at repository root so Yandex Cloud Functions can load
`dynamic_handler.handler` while the bot code remains inside the `bot` package.
"""

from bot.main import handler as bot_handler


async def handler(event: dict, context):
    """Delegate request handling to the bot package handler."""
    return await bot_handler(event, context)
