from fastapi import APIRouter, HTTPException, status
from app.models.schemas import CaseTypeResponse, ErrorResponse
from app.models.case_type_mapping import CASE_TYPE_MAPPING

router = APIRouter()


@router.get(
    "/",
    response_model=CaseTypeResponse,
    status_code=status.HTTP_200_OK,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)
async def get_all_case_types() -> CaseTypeResponse:
    """
    Get all available case types for Kerala Courts.
    
    Returns a mapping of case type IDs to their display names along with the total count.
    """
    try:
        return CaseTypeResponse(
            case_types=CASE_TYPE_MAPPING,
            total_count=len(CASE_TYPE_MAPPING)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve case types: {str(e)}"
        )