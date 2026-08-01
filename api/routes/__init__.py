from fastapi import APIRouter

from api.routes import feed, self_state

router = APIRouter()
router.include_router(self_state.router)
router.include_router(feed.router)
