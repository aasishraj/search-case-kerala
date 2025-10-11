from fastapi import APIRouter, HTTPException, status, Response
from app.models.schemas import (
    CaseFileRequest, CaseFileResponse, CasePDFRequest, 
    CaseJudgementPDFRequest, CaseJudgementPDFResponse,
    ErrorResponse
)
from app.services.kerala_courts_service import KeralaCourtsService

router = APIRouter()
service = KeralaCourtsService()


@router.post(
    "/view",
    response_model=CaseFileResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)
async def get_case_file(request: CaseFileRequest) -> CaseFileResponse:
    """
    Get case file view information.
    
    Requires vieworder token and lookups from case details.
    """
    try:
        return service.get_case_file(request)
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


@router.post(
    "/pdf",
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)
async def download_case_pdf(request: CasePDFRequest) -> Response:
    """
    Download case PDF file.
    
    Requires CINO from a previous case search.
    Returns the PDF file as a download.
    """
    try:
        pdf_response = service.get_case_pdf(request)
        
        return Response(
            content=pdf_response.pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={pdf_response.filename}"
            }
        )
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


@router.get(
    "/interim-pdf",
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)
async def download_interim_pdf(pdf_url: str) -> Response:
    """
    Download interim order PDF from a direct URL.
    
    Requires a PDF URL obtained from case file view.
    Returns the PDF file as a download.
    """
    try:
        pdf_content = service.download_interim_pdf(pdf_url)
        
        # Extract filename from URL or use default
        filename = pdf_url.split('/')[-1] if '/' in pdf_url else "interim_order.pdf"
        
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
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


@router.post(
    "/judgement-pdf",
    response_model=CaseJudgementPDFResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)
async def get_case_judgement_pdf(request: CaseJudgementPDFRequest) -> CaseJudgementPDFResponse:
    """
    Get case judgement PDF URL.
    
    Requires vieworder token from case details.
    Returns the PDF URL and HTML content containing the PDF object.
    """
    try:
        return service.get_case_judgement_pdf(request)
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
