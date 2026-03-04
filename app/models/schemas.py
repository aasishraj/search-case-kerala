from pydantic import BaseModel, Field
from typing import Optional, Dict


class CaseSearchRequest(BaseModel):
    """Request model for case search"""

    case_type_id: str = Field(..., description="Case type ID")
    case_no: str = Field(..., description="Case number", min_length=1)
    case_year: str = Field(..., description="Case year", min_length=4, max_length=4)


class CaseSearchResponse(BaseModel):
    """Response model for case search"""

    cino: str = Field(..., description="Case Information Number")
    case_no: str = Field(..., description="Case number")
    success: bool = Field(..., description="Whether search was successful")


class CaseDetailsRequest(BaseModel):
    """Request model for case details"""

    cino: str = Field(..., description="Case Information Number")
    case_no: str = Field(..., description="Case number")


class CaseDetailsResponse(BaseModel):
    """Response model for case details"""

    cino: str = Field(..., description="Case Information Number")
    case_no: str = Field(..., description="Case number")
    details_html: str = Field(..., description="Case details HTML content")
    vieworder_token: Optional[str] = Field(
        None, description="Vieworder token for file access"
    )
    vieworder_lookups: Optional[str] = Field(
        None, description="Vieworder lookups for file access"
    )


class CaseProceedingsRequest(BaseModel):
    """Request model for case proceedings"""

    cino: str = Field(..., description="Case Information Number")


class CaseProceedingsResponse(BaseModel):
    """Response model for case proceedings"""

    cino: str = Field(..., description="Case Information Number")
    proceedings_html: str = Field(..., description="Case proceedings HTML content")


class CaseFileRequest(BaseModel):
    """Request model for case file access"""

    token: str = Field(..., description="Vieworder token")
    lookups: str = Field(..., description="Vieworder lookups")


class CaseFileResponse(BaseModel):
    """Response model for case file access"""

    token: str = Field(..., description="Vieworder token")
    lookups: str = Field(..., description="Vieworder lookups")
    fileview_html: str = Field(..., description="File view HTML content")
    pdf_url: Optional[str] = Field(None, description="PDF URL if available")


class CasePDFRequest(BaseModel):
    """Request model for case PDF download"""

    cino: str = Field(..., description="Case Information Number")


class CasePDFResponse(BaseModel):
    """Response model for case PDF download"""

    cino: str = Field(..., description="Case Information Number")
    pdf_content: bytes = Field(..., description="PDF file content")
    filename: str = Field(..., description="Suggested filename")


class CaseTypeResponse(BaseModel):
    """Response model for case type"""

    case_types: Dict[int, str] = Field(..., description="Case type mapping")
    total_count: int = Field(..., description="Total count of case types")


class CaseJudgementPDFRequest(BaseModel):
    """Request model for case judgement PDF"""

    token: str = Field(..., description="Vieworder token for judgement PDF access")


class CaseJudgementPDFResponse(BaseModel):
    """Response model for case judgement PDF"""

    pdf_url: Optional[str] = Field(None, description="PDF URL extracted from response")


class ErrorResponse(BaseModel):
    """Error response model"""

    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    status_code: int = Field(..., description="HTTP status code")
