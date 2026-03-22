from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
#from auth.dependencies import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory='templates')


@router.get('/', name='index')
async def index(request: Request):
    return templates.TemplateResponse(request, 'index.html', {})

@router.get('/login')
async def login(request: Request):
    print('[*] Login called')
    return request.url_for(name='auth')