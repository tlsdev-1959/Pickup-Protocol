from fastapi import APIRouter, Request, Depends, HTTPException, Cookie
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from jose import jwt, JWTError, ExpiredSignatureError
import os
import httpx
from datetime import datetime, timezone, timedelta
from dateutil import parser

router = APIRouter()
templates = Jinja2Templates(directory='templates')

async def get_current_user(session: str = Cookie(None)):
    print('[*] Encrypted Cookie: ', session)
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(session, os.getenv('session_secret'), algorithms=["HS384"])
        exp: datetime = datetime.fromtimestamp(payload['exp'])
        return payload
    except ExpiredSignatureError:
        print('[*] Cookie needs to be refreshed')
        raise HTTPException(status_code=504)
    except JWTError:
        raise HTTPException(status_code=401)
    
async def make_bb_call(request: Request, user):
    return

    
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
    bb_schedule_url: str = f'https://api.sky.blackbaud.com/school/v1/schedules/{id}/meetings?start_date={datetime.now().date()}&end_date={datetime.now().date()}'
    bb_headers = {
        'Cache-Control': 'no-cache',
        'Bb-Api-Subscription-Key': os.getenv('bb_subscription'),
        'Authorization': user['access']
    }
    print('[!] Schedule: ', bb_schedule_url)
    print('[*] URL: ', bb_custom_url)
    try:
        async with httpx.AsyncClient() as client:
            bb_response = await client.get(url=bb_url, headers=bb_headers)
            bb_custom_response = await client.get(url=bb_custom_url, headers=bb_headers)
            bb_schedule_response = await client.get(bb_schedule_url, headers=bb_headers)
            #rint(bb_schedule_response.json())
            auth_pickups = [v['text_value'] for v in list(filter(lambda f: f['field_id'] == 3078, bb_custom_response.json()['custom_fields']))]
            lunch_visitors = [v['text_value'] for v in list(filter(lambda f: f['field_id'] == 3098, bb_custom_response.json()['custom_fields']))] 
            at_now = list(filter(lambda f: (parser.parse(f['start_time'], tzinfos=None).isoformat() < datetime.now().isoformat())
                                and (parser.parse(f['end_time'], tzinfos=None).isoformat() > datetime.now().isoformat()), bb_schedule_response.json()['value']))
            if not len(at_now):
                at_now = bb_schedule_response.json()['value'][-1]
    except httpx.ReadTimeout:
        print('[*] Timed out')
        return RedirectResponse(url=str(request.url_for('get_student_by_user_id', id)))

    return JSONResponse({'student': bb_response.json(), 'pickups': auth_pickups, 'visitors': lunch_visitors, 'schedule': bb_schedule_response.json()['value'], 'At now': at_now})





@router.get('/search/byname', name='name_search')
async def searchByName(request: Request, user=Depends(get_current_user)):
    return JSONResponse({'name': 'Tanner'})


@router.get('/grades', name='get_env_grades')
async def getGrades(request: Request, user=Depends(get_current_user)):
    return