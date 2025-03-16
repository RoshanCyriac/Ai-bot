from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

# Create router
router = APIRouter()

# Setup template directory
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def serve_frontend(request: Request):
    """Serve the main frontend page"""
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/test-general-chat", response_class=HTMLResponse)
async def test_general_chat(request: Request):
    """Serve the test general chat page"""
    return templates.TemplateResponse("test-general-chat.html", {"request": request})

@router.get("/test-reminders", response_class=HTMLResponse)
async def test_reminders(request: Request):
    """Serve the test reminders UI page"""
    return templates.TemplateResponse("test_reminders_ui.html", {"request": request}) 