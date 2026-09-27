"""FastAPI routers — Layer 1 (HTTP 边界).

约定：
- 路由函数全部 `async def`
- 通过 Depends(get_session) 拿到 AsyncSession
- 不感知 ORM 模型细节（转 DTO）
"""

from app.api.healthz import router as healthz_router
from app.api.projects import router as projects_router
from app.api.router import router as intent_router_router
from app.api.write import router as write_router

__all__ = [
    "healthz_router",
    "projects_router",
    "write_router",
    "intent_router_router",
]