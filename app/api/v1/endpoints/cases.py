from fastapi import APIRouter, HTTPException, status
from app.models.schemas import CaseSearchRequest, CaseSearchResponse, ErrorResponse
from app.services.kerala_courts_service import KeralaCourtsService

router = APIRouter()
service = KeralaCourtsService()


@router.post(
    "/search",
    response_model=CaseSearchResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)
async def search_case(request: CaseSearchRequest) -> CaseSearchResponse:
    """
    Search for a case by type, number, and year.
    
    Returns the CINO (Case Information Number) and case number if found.
    """
    try:
        return service.search_case(request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
