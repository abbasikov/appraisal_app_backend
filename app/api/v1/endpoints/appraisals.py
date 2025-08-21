from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_appraisals():
    return {"message": "Appraisals endpoint"}

@router.post("/")
async def create_appraisal():
    return {"message": "Create appraisal endpoint"}