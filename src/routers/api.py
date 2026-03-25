from fastapi import APIRouter, Request, Depends, HTTPException, Cookie
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from jose import jwt, JWTError
import os
import httpx

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

    
@router.get('/me/profile/picture', name='my_picture')
async def getMyProfilePicture(request: Request, user=Depends(get_current_user)):
    bb_url: str = f'https://api.sky.blackbaud.com/school/v1/users/{user['user']}'
    bb_headers = {
        'Cache-Control': 'no-cache',
        'Bb-Api-Subscription-Key': os.getenv('bb_subscription'),
        'Authorization': user['access']
    }
    async with httpx.AsyncClient() as client:
        bb_response = await client.get(url=bb_url, headers=bb_headers)
    out_url = 'https:'+bb_response.json()['profile_pictures']['thumb_filename_url']
    return JSONResponse({"url": out_url})


## Student API ##

@router.get('/student', name='get_student_by_user_id')
async def studentById(request: Request, id: int, user=Depends(get_current_user)):
    bb_url: str = f'https://api.sky.blackbaud.com/school/v1/users/{id}'
    bb_custom_url: str = f'https://api.sky.blackbaud.com/school/v1/users/{id}/customfields'
    bb_headers = {
        'Cache-Control': 'no-cache',
        'Bb-Api-Subscription-Key': os.getenv('bb_subscription'),
        'Authorization': user['access']
    }
    print('[*] URL: ', bb_custom_url)
    async with httpx.AsyncClient() as client:
        bb_response = await client.get(url=bb_url, headers=bb_headers)
        bb_custom_response = await client.get(url=bb_custom_url, headers=bb_headers)
        print(bb_custom_response.json())
        auth_pickups = [v['text_value'] for v in list(filter(lambda f: f['field_id'] == 3078, bb_custom_response.json()['custom_fields']))]
        lunch_visitors = [v['text_value'] for v in list(filter(lambda f: f['field_id'] == 3098, bb_custom_response.json()['custom_fields']))] 
        print('[*] Auth pickups: ', auth_pickups)
        print('[*] Type: ', type(bb_response.json()))
    return JSONResponse({'student': bb_response.json(), 'pickups': auth_pickups, 'visitors': lunch_visitors})





@router.get('/search/byname', name='name_search')
async def searchByName(request: Request, user=Depends(get_current_user)):
    return JSONResponse({'name': 'Tanner'})


@router.get('/grades', name='get_env_grades')
async def getGrades(request: Request, user=Depends(get_current_user)):
    return