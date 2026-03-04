from fastapi import APIRouter
from app.api.v1.endpoints import (
    cases,
    case_details,
    case_proceedings,
    case_files,
    case_type,
)

api_router = APIRouter()

api_router.include_router(cases.router, prefix="/cases", tags=["cases"])
api_router.include_router(
    case_details.router, prefix="/case-details", tags=["case-details"]
)
api_router.include_router(
    case_proceedings.router, prefix="/case-proceedings", tags=["case-proceedings"]
)
api_router.include_router(case_files.router, prefix="/case-files", tags=["case-files"])
api_router.include_router(case_type.router, prefix="/case-types", tags=["case-types"])
