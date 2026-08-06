from fastapi import APIRouter

from app.api.v1.endpoints import admin, auth, customer, driver, webhooks, iot, franchise

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(customer.router, prefix="", tags=["customer"])
api_router.include_router(driver.router, prefix="/drivers", tags=["drivers"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
api_router.include_router(iot.router, prefix="/iot", tags=["iot"])
api_router.include_router(franchise.router, prefix="/franchise", tags=["franchise"])
