"""Совместимый фасад для common handlers.

Основная реализация разнесена на:
- bot.handlers.common_feature.services
- bot.handlers.common_feature.views
- bot.handlers.common_feature.handlers
"""

from .common_feature.handlers import *  # noqa: F401,F403