from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_properties():
    return {"message": "Properties endpoint"}

@router.post("/")
async def create_property():
    return {"message": "Create property endpoint"}