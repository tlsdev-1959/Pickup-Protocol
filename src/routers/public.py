from fastapi import APIRouter, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse
#from auth.dependencies import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory='templates')


@router.get('/', name='index')
async def index(request: Request):
    try:
        print(request.cookies['session'] != None)
        return RedirectResponse(url=str(request.url_for('home')), status_code=303)
    except KeyError: # session not found
        return templates.TemplateResponse(request, 'index.html', {})

#@router.get('/login', name='login')
#async def login(request: Request):
#    print('[*] Login called')
#    return RedirectResponse(url=request.url_for('auth'), status_code=303)

@router.get('/login/failed/permission/error', name='access_denied')
async def showDeniedAccess(request: Request):
    return templates.TemplateResponse(request, 'access_denied.html', {})

@router.get('/debug-cookies')
async def debug_cookies(request: Request):
    return {"cookies": request.cookies}