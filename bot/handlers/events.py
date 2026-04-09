"""Сборка сценариев мероприятий: create/edit/cancel/category/carpool."""

from aiogram import Router

from .event_scenarios.create import router as create_router
from .event_scenarios.carpool import router as carpool_router
from .event_scenarios.category import router as category_router
from .event_scenarios.edit import router as edit_router
from .event_scenarios.cancel import router as cancel_router

router = Router(name=__name__)
router.include_router(create_router)
router.include_router(carpool_router)
router.include_router(category_router)
router.include_router(edit_router)
router.include_router(cancel_router)