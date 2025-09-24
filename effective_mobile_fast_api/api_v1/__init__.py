from fastapi import APIRouter

from effective_mobile_fast_api.api_v1.admin.admin_views import router as admin_router
from effective_mobile_fast_api.api_v1.auth.views import router as auth_router
from effective_mobile_fast_api.api_v1.users.views import router as users_router
from effective_mobile_fast_api.api_v1.business.views import router as business_router
from effective_mobile_fast_api.api_v1.web.views import router as web_router

router = APIRouter()
router.include_router(router=users_router, prefix="/users")
router.include_router(router=auth_router, prefix="/auth")
router.include_router(router=admin_router, prefix="/admin")
router.include_router(router=business_router, prefix="/business")
router.include_router(router=web_router)
