import requests
import re
import json
from typing import Optional, Tuple
from app.models.schemas import (
    CaseSearchRequest, CaseSearchResponse,
    CaseDetailsRequest, CaseDetailsResponse,
    CaseProceedingsRequest, CaseProceedingsResponse,
    CaseFileRequest, CaseFileResponse,
    CasePDFRequest, CasePDFResponse
)


class KeralaCourtsService:
    """Service class for interacting with Kerala Courts API"""
    
    BASE_URL = "https://hckinfo.keralacourts.in"
    FIRST_URI = f"{BASE_URL}/digicourt/Casedetailssearch/Statuscasenovoice"
    SECOND_URI = f"{BASE_URL}/digicourt/index.php/Casedetailssearch/Stausbycaseno"
    THIRD_URI = f"{BASE_URL}/digicourt/index.php/Casedetailssearch/Viewcasestatus"
    FOURTH_URI = f"{BASE_URL}/digicourt/index.php/Queryproceedings/getProceedings"
    FIFTH_URI = f"{BASE_URL}/digicourt/Casedetailssearch/printz"
    SIXTH_URI = f"{BASE_URL}/digicourt/Casedetailssearch/fileview"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def _extract_case_params(self, response_text: str) -> Optional[Tuple[str, str]]:
        """Extract cino and case_no from search response."""
        try:
            data = json.loads(response_text)
            html = data.get('p_table', '')
        except (json.JSONDecodeError, KeyError):
            html = response_text
        
        match = re.search(r"ViewCaseStatus\('([^']+)',\s*'([^']+)'", html)
        return (match.group(1), match.group(2)) if match else None

    def _extract_vieworder_params(self, html_content: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract token and lookups parameters from vieworder function calls."""
        pattern = r"vieworder\('([^']+)',\s*'([^']+)',\s*'([^']*)'\)"
        matches = re.findall(pattern, html_content)
        
        if matches:
            token, lookups, rootuser = matches[0]
            return token, lookups
        return None, None

    def _extract_pdf_url(self, html_content: str) -> Optional[str]:
        """Extract PDF URL from object data attribute."""
        pattern = r'<object data="([^"]+\.pdf)"'
        match = re.search(pattern, html_content)
        return match.group(1) if match else None

    def search_case(self, request: CaseSearchRequest) -> CaseSearchResponse:
        """Search for a case by type, number, and year"""
        try:
            response = self.session.post(
                self.SECOND_URI,
                data={
                    'case_type': int(request.case_type_id),
                    'case_no': int(request.case_no),
                    'case_year': int(request.case_year),
                },
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'X-Requested-With': 'XMLHttpRequest',
                    'Referer': self.FIRST_URI
                },
                timeout=30
            )
            response.raise_for_status()
            
            case_params = self._extract_case_params(response.text)
            
            if not case_params:
                raise ValueError("No case parameters found in response")
            
            cino, case_no = case_params
            return CaseSearchResponse(
                cino=cino,
                case_no=case_no,
                success=True
            )
            
        except requests.RequestException as e:
            raise ValueError(f"Failed to search case: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error processing case search: {str(e)}")

    def get_case_details(self, request: CaseDetailsRequest) -> CaseDetailsResponse:
        """Get detailed case information"""
        try:
            response = self.session.post(
                self.THIRD_URI,
                data={
                    'cino': request.cino,
                    'case_no': request.case_no
                },
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'X-Requested-With': 'XMLHttpRequest',
                    'Referer': self.FIRST_URI
                },
                timeout=30
            )
            response.raise_for_status()
            
            token, lookups = self._extract_vieworder_params(response.text)
            
            return CaseDetailsResponse(
                cino=request.cino,
                case_no=request.case_no,
                details_html=response.text,
                vieworder_token=token,
                vieworder_lookups=lookups
            )
            
        except requests.RequestException as e:
            raise ValueError(f"Failed to get case details: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error processing case details: {str(e)}")

    def get_case_proceedings(self, request: CaseProceedingsRequest) -> CaseProceedingsResponse:
        """Get case proceedings"""
        try:
            response = self.session.post(
                self.FOURTH_URI,
                data={'cinoz': request.cino},
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'X-Requested-With': 'XMLHttpRequest',
                    'Referer': self.FIRST_URI
                },
                timeout=30
            )
            response.raise_for_status()
            
            return CaseProceedingsResponse(
                cino=request.cino,
                proceedings_html=response.text
            )
            
        except requests.RequestException as e:
            raise ValueError(f"Failed to get case proceedings: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error processing case proceedings: {str(e)}")

    def get_case_pdf(self, request: CasePDFRequest) -> CasePDFResponse:
        """Download case PDF"""
        try:
            pdf_uri = f"{self.FIFTH_URI}/{request.cino}"
            response = self.session.get(
                pdf_uri,
                headers={'Referer': self.FIRST_URI},
                timeout=30
            )
            response.raise_for_status()
            
            return CasePDFResponse(
                cino=request.cino,
                pdf_content=response.content,
                filename=f"case_{request.cino}.pdf"
            )
            
        except requests.RequestException as e:
            raise ValueError(f"Failed to download case PDF: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error processing case PDF: {str(e)}")

    def get_case_file(self, request: CaseFileRequest) -> CaseFileResponse:
        """Get case file view"""
        try:
            fileview_uri = f"{self.SIXTH_URI}?token={request.token}&lookups={request.lookups}"
            response = self.session.get(
                fileview_uri,
                headers={'Referer': self.FIRST_URI},
                timeout=30
            )
            response.raise_for_status()
            
            pdf_url = self._extract_pdf_url(response.text)
            
            return CaseFileResponse(
                token=request.token,
                lookups=request.lookups,
                fileview_html=response.text,
                pdf_url=pdf_url
            )
            
        except requests.RequestException as e:
            raise ValueError(f"Failed to get case file: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error processing case file: {str(e)}")

    def download_interim_pdf(self, pdf_url: str) -> bytes:
        """Download interim order PDF from URL"""
        try:
            response = self.session.get(
                pdf_url,
                headers={'Referer': self.FIRST_URI},
                timeout=30
            )
            response.raise_for_status()
            return response.content
            
        except requests.RequestException as e:
            raise ValueError(f"Failed to download interim PDF: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error downloading interim PDF: {str(e)}")
