from fastapi import APIRouter, HTTPException, status
from app.models.schemas import CaseDetailsRequest, CaseDetailsResponse, ErrorResponse
from app.services.kerala_courts_service import KeralaCourtsService

router = APIRouter()
service = KeralaCourtsService()


@router.post(
    "/",
    response_model=CaseDetailsResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
async def get_case_details(request: CaseDetailsRequest) -> CaseDetailsResponse:
    """
    Get detailed case information including HTML content and vieworder parameters.

    Requires CINO and case number from a previous case search.
    """
    try:
        return service.get_case_details(request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )
