"""Совместимый фасад для split-bill handlers.

Основная реализация разнесена на:
- bot.handlers.split_bill_feature.services
- bot.handlers.split_bill_feature.views
- bot.handlers.split_bill_feature.handlers
"""

from .split_bill_feature.handlers import *  # noqa: F401,F403