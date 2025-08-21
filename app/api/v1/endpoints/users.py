from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_users():
    return {"message": "Users endpoint"}

@router.post("/")
async def create_user():
    return {"message": "Create user endpoint"}