from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
#from auth.dependencies import get_current_user

router = APIRouter()
templates = Jinja2Templates('../templates')

@router.get('/login')
async def login(request: Request):
    print('[*] Login called')
    return request.url_for(name='auth')