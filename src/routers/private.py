from fastapi import APIRouter, Request, Depends, HTTPException, Cookie
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse
from jose import jwt, JWTError
import os

router = APIRouter()
templates = Jinja2Templates(directory='templates')

async def get_current_user(session: str = Cookie(None)):
    print(session)
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(session, os.getenv('session_secret'), algorithms=["HS256"])
        return payload
    except JWTError:
        raise HTTPException(status_code=401)


@router.get('/', name='home')
async def home(request: Request, user=Depends(get_current_user)):
        print(user)
        return templates.TemplateResponse(request, 'home.html', {'user': user, 'preferred': user['preferred']})
    

