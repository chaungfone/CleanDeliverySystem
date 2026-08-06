from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.database import get_supabase_client
from app.core.security import CurrentUser, require_roles
from app.models.user import UserRole

router = APIRouter(dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.BRANCH_MANAGER))])

class FranchiseCreate(BaseModel):
    owner_id: str = Field(..., pattern=r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
    business_name: str = Field(..., min_length=1, max_length=255)
    region: str = Field(..., min_length=1, max_length=255)

@router.get("/stats")
def get_franchise_stats(user: CurrentUser):
    """Returns commission and sales stats for the dealer's franchise."""
    # In production, filter by user.branch_id or franchise link
    return {
        "business_name": "Apex Water Dealers",
        "total_sales": 1500000,
        "commission_earned": 150000,
        "active_drivers": 5
    }

@router.get("/wholesale/catalog")
def get_wholesale_catalog():
    """Returns products with special dealer pricing."""
    db = get_supabase_client()
    # Mock wholesale logic: 20% discount
    products = db.table("products").select("*").execute().data
    for p in products:
        p["wholesale_price"] = float(p["price"]) * 0.8
    return products
