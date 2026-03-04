from fastapi import APIRouter, HTTPException, status
from app.models.schemas import (
    CaseProceedingsRequest,
    CaseProceedingsResponse,
    ErrorResponse,
)
from app.services.kerala_courts_service import KeralaCourtsService

router = APIRouter()
service = KeralaCourtsService()


@router.post(
    "/",
    response_model=CaseProceedingsResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
async def get_case_proceedings(
    request: CaseProceedingsRequest,
) -> CaseProceedingsResponse:
    """
    Get case proceedings information.

    Requires CINO from a previous case search.
    """
    try:
        return service.get_case_proceedings(request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )
