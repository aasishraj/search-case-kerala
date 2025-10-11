#!/usr/bin/env python3
"""
Simple script to search Kerala Courts case information.
"""

import requests
import re
import json


def extract_case_params(response_text):
    """Extract cino and case_no from search response."""
    try:
        data = json.loads(response_text)
        html = data.get('p_table', '')
    except (json.JSONDecodeError, KeyError):
        html = response_text
    
    match = re.search(r"ViewCaseStatus\('([^']+)',\s*'([^']+)'", html)
    return (match.group(1), match.group(2)) if match else None


def extract_vieworder_params(html_content):
    """Extract token and lookups parameters from vieworder function calls."""
    # Find all vieworder function calls with parameters
    pattern = r"vieworder\('([^']+)',\s*'([^']+)',\s*'([^']*)'\)"
    matches = re.findall(pattern, html_content)
    
    if matches:
        # Return the first match (token, lookups, rootuser)
        token, lookups, rootuser = matches[0]
        return token, lookups
    return None, None


def extract_pdf_url(html_content):
    """Extract PDF URL from object data attribute."""
    pattern = r'<object data="([^"]+\.pdf)"'
    match = re.search(pattern, html_content)
    return match.group(1) if match else None


def main():
    BASE_URL = "https://hckinfo.keralacourts.in"
    FIRST_URI = f"{BASE_URL}/digicourt/Casedetailssearch/Statuscasenovoice"
    SECOND_URI = f"{BASE_URL}/digicourt/index.php/Casedetailssearch/Stausbycaseno"
    THIRD_URI = f"{BASE_URL}/digicourt/index.php/Casedetailssearch/Viewcasestatus"
    FOURTH_URI = f"{BASE_URL}/digicourt/index.php/Queryproceedings/getProceedings"
    FIFTH_URI = f"{BASE_URL}/digicourt/Casedetailssearch/printz"
    SIXTH_URI = f"{BASE_URL}/digicourt/Casedetailssearch/fileview"
    
    # Case search parameters
    CASE_TYPE = "154"
    CASE_NO = "1521"
    CASE_YEAR = "2011"
    
    # Create session to maintain cookies
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    # Step 3: Submit search to second URI
    print(f"Step 3: Searching case (Type={CASE_TYPE}, No={CASE_NO}, Year={CASE_YEAR})...")
    search_response = session.post(
        SECOND_URI,
        data={
            'case_type': CASE_TYPE,
            'case_no': CASE_NO,
            'case_year': CASE_YEAR,
        },
        headers={
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': FIRST_URI
        },
        timeout=30
    )
    search_response.raise_for_status()
    
    # Save search response
    with open('search_response.html', 'w', encoding='utf-8') as f:
        f.write(search_response.text)
    print("Search response saved to search_response.html")
    
    # Step 4: Extract case parameters from search response
    print("Step 4: Extracting case parameters...")
    case_params = extract_case_params(search_response.text)
    
    if not case_params:
        print("ERROR: No case parameters found")
        return
    
    cino, case_no = case_params
    print(f"Found CINO: {cino}, Case No: {case_no}")
    
    # Step 5: Get detailed case info from third URI
    print("Step 5: Fetching detailed case information...")
    details_response = session.post(
        THIRD_URI,
        data={
            'cino': cino,
            'case_no': case_no
        },
        headers={
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': FIRST_URI
        },
        timeout=30
    )
    details_response.raise_for_status()
    
    # Save case details
    with open('case_details.html', 'w', encoding='utf-8') as f:
        f.write(details_response.text)
    print("Case details saved to case_details.html")
    
    # Step 6: Get case proceedings from fourth URI
    print("Step 6: Fetching case proceedings...")
    proceedings_response = session.post(
        FOURTH_URI,
        data={'cinoz': cino},
        headers={
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': FIRST_URI
        },
        timeout=30
    )
    proceedings_response.raise_for_status()
    
    # Save case proceedings
    with open('case_proceedings.html', 'w', encoding='utf-8') as f:
        f.write(proceedings_response.text)
    print("Case proceedings saved to case_proceedings.html")
    
    # Step 7: Download PDF from fifth URI
    print("Step 7: Downloading case PDF...")
    pdf_uri = f"{FIFTH_URI}/{cino}"
    pdf_response = session.get(
        pdf_uri,
        headers={'Referer': FIRST_URI},
        timeout=30
    )
    pdf_response.raise_for_status()
    
    # Save PDF file
    pdf_filename = f"case_{cino}.pdf"
    with open(pdf_filename, 'wb') as f:
        f.write(pdf_response.content)
    print(f"Case PDF saved as {pdf_filename}")
    
    # Step 8: Extract vieworder parameters from case details
    print("Step 8: Extracting vieworder parameters...")
    with open('case_details.html', 'r', encoding='utf-8') as f:
        case_details_html = f.read()
    
    token, lookups = extract_vieworder_params(case_details_html)
    
    if token and lookups:
        print(f"Found vieworder parameters - Token: {token}, Lookups: {lookups}")
        
        # Step 9: Get fileview response
        print("Step 9: Fetching fileview response...")
        fileview_uri = f"{SIXTH_URI}?token={token}&lookups={lookups}"
        fileview_response = session.get(
            fileview_uri,
            headers={'Referer': FIRST_URI},
            timeout=30
        )
        fileview_response.raise_for_status()
        
        # Save fileview response
        with open('fileview_response.html', 'w', encoding='utf-8') as f:
            f.write(fileview_response.text)
        print("Fileview response saved to fileview_response.html")
        
        # Step 10: Extract and download PDF from fileview response
        print("Step 10: Extracting PDF URL from fileview response...")
        pdf_url = extract_pdf_url(fileview_response.text)
        
        if pdf_url:
            print(f"Found PDF URL: {pdf_url}")
            
            # Download the PDF
            print("Downloading interim order PDF...")
            interim_pdf_response = session.get(
                pdf_url,
                headers={'Referer': FIRST_URI},
                timeout=30
            )
            interim_pdf_response.raise_for_status()
            
            # Save interim order PDF
            interim_pdf_filename = f"interim_order_{cino}.pdf"
            with open(interim_pdf_filename, 'wb') as f:
                f.write(interim_pdf_response.content)
            print(f"Interim order PDF saved as {interim_pdf_filename}")
        else:
            print("No PDF URL found in fileview response")
    else:
        print("No vieworder parameters found in case details")
    
    print("Done! All files downloaded successfully.")


if __name__ == "__main__":
    main()
