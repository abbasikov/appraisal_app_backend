from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_reports():
    return {"message": "Reports endpoint"}

@router.post("/generate")
async def generate_report():
    return {"message": "Generate report endpoint"}