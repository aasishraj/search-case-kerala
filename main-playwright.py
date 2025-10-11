from __future__ import annotations

import asyncio
import json
import os
import time
import uuid
from io import BytesIO
from typing import Any, Dict, Optional, Set, Tuple

from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from playwright.async_api import Browser, BrowserContext, Page, async_playwright
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field
from constants import CASE_TYPES


APP_TITLE = "Kerala Courts Case Search API"
START_URL = "https://hckinfo.keralacourts.in/digicourt/Casedetailssearch/Statuscasenovoice"
SEARCH_XHR_PATH_FRAGMENT = "/Casedetailssearch/Stausbycaseno"
SESSION_TTL_SECONDS = 15 * 60

# Headless-stealth configuration to appear like a real GUI browser
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/119.0.0.0 Safari/537.36"
)
VIEWPORT = {"width": 1366, "height": 768}
LOCALE = "en-US"
EXTRA_HEADERS = {
    "Accept-Language": "en-US,en;q=0.9",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-User": "?1",
    "Sec-Fetch-Dest": "document",
}
STEALTH_LAUNCH_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    "--disable-infobars",
    "--disable-dev-shm-usage",
]


class SessionEntry:
    def __init__(self, context: BrowserContext, page: Page) -> None:
        self.context = context
        self.page = page
        self.created_at = time.time()

    def is_expired(self) -> bool:
        return (time.time() - self.created_at) > SESSION_TTL_SECONDS


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.playwright = await async_playwright().start()
    app.state.browser = await app.state.playwright.chromium.launch(
        headless=True,
        args=STEALTH_LAUNCH_ARGS,
    )
    app.state.sessions: Dict[str, SessionEntry] = {}
    app.state.case_types: Set[str] = CASE_TYPES
    app.state.sweeper_task = asyncio.create_task(_sweeper())
    try:
        yield
    finally:
        # Shutdown
        sweeper_task: asyncio.Task = app.state.sweeper_task
        sweeper_task.cancel()
        try:
            await sweeper_task
        except Exception:
            pass

        sessions: Dict[str, SessionEntry] = app.state.sessions
        for sid, entry in list(sessions.items()):
            try:
                await entry.context.close()
            except Exception:
                pass
            sessions.pop(sid, None)

        try:
            browser: Browser = app.state.browser
            await browser.close()
        except Exception:
            pass
        try:
            await app.state.playwright.stop()
        except Exception:
            pass


app = FastAPI(title=APP_TITLE, lifespan=lifespan)


async def _sweeper() -> None:
    """Background task to cleanup expired sessions."""
    while True:
        try:
            await asyncio.sleep(30)
            sessions: Dict[str, SessionEntry] = app.state.sessions
            to_delete = [sid for sid, s in sessions.items() if s.is_expired()]
            for sid in to_delete:
                entry = sessions.pop(sid, None)
                if entry:
                    try:
                        await entry.context.close()
                    except Exception:
                        pass
        except asyncio.CancelledError:
            break
        except Exception:
            continue


def _resolve_session_id(
    request: Request, x_session_id: Optional[str], session_id_q: Optional[str]
) -> str:
    sid = x_session_id or session_id_q
    if not sid:
        sid = request.cookies.get("session_id")
    if not sid:
        raise HTTPException(
            status_code=400,
            detail="Missing session_id. Provide 'X-Session-Id' header or 'session_id' query param."
        )
    return sid


async def _create_session() -> Tuple[str, SessionEntry]:
    browser: Browser = app.state.browser
    context = await browser.new_context(
        user_agent=USER_AGENT,
        viewport=VIEWPORT,
        locale=LOCALE,
    )
    await context.set_extra_http_headers(EXTRA_HEADERS)
    await context.add_init_script(
        """
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        """
    )

    page = await context.new_page()
    await page.goto(START_URL, wait_until="domcontentloaded")
    entry = SessionEntry(context=context, page=page)
    sid = uuid.uuid4().hex
    app.state.sessions[sid] = entry
    return sid, entry


async def _select_case_type(page: Page, case_type: str) -> None:
    selected = await page.select_option("#case_type", label=case_type)
    if selected:
        return
    options = page.locator("#case_type option")
    count = await options.count()
    for i in range(count):
        text = (await options.nth(i).text_content() or "").strip()
        value = (await options.nth(i).get_attribute("value") or "").strip()
        if case_type in text or case_type == value:
            sel = await page.select_option("#case_type", value=value)
            if sel:
                return
    raise HTTPException(
        status_code=400,
        detail=f"Unable to select case_type '{case_type}' on the page."
    )


@app.get("/get-captcha")
async def get_captcha() -> StreamingResponse:
    sid, entry = await _create_session()
    page = entry.page
    img = page.locator("#captcha_image img")
    await img.wait_for(state="visible")
    src = await img.get_attribute("src")
    if not src:
        raise HTTPException(status_code=500, detail="Captcha image not found.")

    resp = await entry.context.request.get(src)
    if not resp.ok:
        raise HTTPException(status_code=502, detail="Failed to fetch captcha image.")
    content_type = resp.headers.get("content-type", "image/jpeg")
    data = await resp.body()
    filename = os.path.basename(src.split("?")[0]) or "captcha.jpg"

    headers = {
        "X-Session-Id": sid,
        "Content-Disposition": f'inline; filename="{filename}"',
    }
    return StreamingResponse(BytesIO(data), media_type=content_type, headers=headers)


# FIXED: moved Pydantic model OUTSIDE the decorator
class GetCaseInfoRequest(BaseModel):
    case_type: str = Field(..., description="Case type; must match an entry in case-types.txt")
    case_number: str = Field(..., description="Case number as shown on the site")
    year: str = Field(..., description="Four-digit year, e.g., 2011")
    captcha_text: Optional[str] = Field(None, description="Captcha solution for the session")


class GetCaseInfoResponse(BaseModel):
    session_id: str
    result: Optional[Dict[str, Any]] = None
    html: Optional[str] = None


@app.post("/get-case-info", response_model=GetCaseInfoResponse)
async def get_case_info(
    request: Request,
    payload: GetCaseInfoRequest,
    x_session_id: Optional[str] = Header(default=None, alias="X-Session-Id"),
    session_id_q: Optional[str] = Query(default=None, alias="session_id"),
) -> GetCaseInfoResponse:
    case_type = payload.case_type.strip()
    case_number = payload.case_number.strip()
    case_year = payload.year.strip()
    captcha_text = payload.captcha_text

    if not case_type or not case_number or not case_year:
        raise HTTPException(
            status_code=400,
            detail="Fields 'case_type', 'case_number', and 'year' are required."
        )

    allowed: Set[str] = CASE_TYPES
    if allowed and case_type not in allowed:
        raise HTTPException(
            status_code=422,
            detail="Invalid 'case_type'. See case-types.txt for allowed values."
        )

    sid = _resolve_session_id(request, x_session_id, session_id_q)
    session: Optional[SessionEntry] = app.state.sessions.get(sid)
    if session is None or session.is_expired():
        raise HTTPException(status_code=404, detail="Session not found or expired. Call /get-captcha again.")

    page = session.page
    try:
        if not await page.locator("#case_type").count():
            await page.goto(START_URL, wait_until="domcontentloaded")
    except Exception:
        await page.goto(START_URL, wait_until="domcontentloaded")

    await _select_case_type(page, case_type)
    await page.fill("#case_no", case_number)
    await page.fill("#case_year", case_year)

    captcha_input = page.locator(
        "input[placeholder*=Captcha i], input[name*=captcha i], input[id*=captcha i]"
    ).first
    try:
        if await captcha_input.count():
            if not captcha_text:
                raise HTTPException(status_code=400, detail="'captcha_text' is required for this session.")
            await captcha_input.fill(str(captcha_text))
    except HTTPException:
        raise
    except Exception:
        pass

    def _is_target(resp) -> bool:
        try:
            return SEARCH_XHR_PATH_FRAGMENT in resp.url and resp.request.method.upper() == "POST"
        except Exception:
            return False

    async with page.expect_response(_is_target, timeout=15000) as resp_info:
        await page.locator('button:has-text("SEARCH")').click()
    xhr_resp = await resp_info.value

    try:
        result = await xhr_resp.json()
    except Exception:
        text = await xhr_resp.text()
        try:
            result = json.loads(text)
        except Exception:
            try:
                html = await page.locator("#casedetails").inner_html()
            except Exception:
                html = await page.content()
            result = {"html": html}

    if isinstance(result, dict):
        return GetCaseInfoResponse(session_id=sid, result=result)
    if isinstance(result, str):
        return GetCaseInfoResponse(session_id=sid, html=result)
    return GetCaseInfoResponse(session_id=sid, result={"raw": result})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)