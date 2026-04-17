from fastapi import APIRouter, Request, Depends, HTTPException, Cookie, Security
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
import json
from jose import jwt, JWTError, ExpiredSignatureError
import os
import httpx
import re
from datetime import datetime, timezone, timedelta
from dateutil import parser
from routers import auth
from objects.student import Student
import pandas as pd
import numpy as np
import asyncio
from queue import Queue

router = APIRouter()
templates = Jinja2Templates(directory='templates')

_picture_cache: dict[int, tuple[str, datetime]] = {}  # {user_id: (url, expires_at)}

_picture_cache_max_age_seconds = 3600

async def get_current_user(session: str = Cookie(None)):
    #print('[*] Encrypted Cookie: ', session)
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(session, os.getenv('session_secret'), algorithms=["HS384"])
        return payload
    except ExpiredSignatureError:
        raise HTTPException(status_code=504)
    except JWTError:
        raise HTTPException(status_code=401)
    

    
async def make_bb_get_call(actor: dict , bb_url: str, bb_headers: dict = None, num_attempts: int = 0, client: httpx.AsyncClient = None):
    
    if bb_headers is None:
        bb_headers = {
            'Cache-Control': 'no-cache',
            'Bb-Api-Subscription-Key': os.getenv('bb_subscription'),
            'Authorization': actor['access']
        }
    
    try:
        if client is None:
            async with httpx.AsyncClient() as c:
                bb_response = await c.get(url=bb_url, headers=bb_headers)
        else:
            bb_response = await client.get(url=bb_url, headers=bb_headers)
        #print(await auth.refresh_bb(actor['refresh']))
        return bb_response
    except httpx.ReadTimeout:
        if num_attempts > 3:
            raise HTTPException(status_code=503)
        else:
            return make_bb_get_call(actor, bb_url, bb_headers, num_attempts + 1)
        

async def make_bb_sys_get_call(actor: dict, bb_url: str, num_attempts: int = 0, client: httpx.AsyncClient = httpx.AsyncClient()):
    try:
        bb_headers = {
            'Cache-Control': 'no-cache',
            'Bb-Api-Subscription-Key': os.getenv('bb_subscription'),
            'Authorization': actor['access']
        }
        async with httpx.AsyncClient() as client:
            bb_response = await client.get(url=bb_url, headers=bb_headers)
        print(bb_response)
        return bb_response
    except httpx.ReadTimeout:
        if num_attempts > 3:
            raise HTTPException(status_code=503)
        else:
            return make_bb_sys_get_call(actor, bb_url, bb_headers, num_attempts + 1)


@router.get('/me/profile/picture', name='my_picture')
async def getMyProfilePicture(request: Request, user=Security(get_current_user)):
    
    user_id: int = user['user']
    cached = _picture_cache.get(user_id)
    if cached and cached[1] > datetime.now():
        return JSONResponse({"url": cached[0]}, headers={"Cache-Control": f"max-age={_picture_cache_max_age_seconds}, private"})

    bb_url: str = f'https://api.sky.blackbaud.com/school/v1/users/{user_id}'
    bb_headers = {
        'Cache-Control': 'no-cache',
        'Bb-Api-Subscription-Key': os.getenv('bb_subscription'),
        'Authorization': user['access']
    }
    bb_response = await make_bb_get_call(user, bb_url, bb_headers)
    out_url = 'https:' + bb_response.json()['profile_pictures']['thumb_filename_url']
    _picture_cache[user_id] = (out_url, datetime.now() + timedelta(seconds=_picture_cache_max_age_seconds))
    return JSONResponse({"url": out_url}, headers={"Cache-Control": f"max-age={_picture_cache_max_age_seconds}, private"})


## Student API ##

@router.get('/student/{id}', name='get_student_by_user_id')
async def studentById(request: Request, id: int, user=Security(get_current_user)):
    #print(request.session)
    bb_url: str = f'https://api.sky.blackbaud.com/school/v1/users/extended/{id}'
    bb_custom_url: str = f'https://api.sky.blackbaud.com/school/v1/users/{id}/customfields'
    bb_schedule_url: str = f'https://api.sky.blackbaud.com/school/v1/schedules/{id}/meetings?start_date={datetime.now().date()}&end_date={datetime.now().date()}'
    bb_headers = {
        'Cache-Control': 'no-cache',
        'Bb-Api-Subscription-Key': os.getenv('bb_subscription'),
        'Authorization': user['access']
    }
    try:
        async with httpx.AsyncClient() as client:
            bb_response, bb_custom_response, bb_schedule_response = await asyncio.gather(
                make_bb_get_call(user, bb_url=bb_url, client=client),
                make_bb_get_call(user, bb_url=bb_custom_url, client=client),
                make_bb_get_call(user, bb_url=bb_schedule_url, client=client),
            )
        parent_mask = np.vectorize(lambda f: f['contact'] and f['parental_access'])
        relationships = np.array(bb_response.json()['relationships'])
        parents = relationships[parent_mask(relationships)]
        #parents = list(filter(lambda f: f['contact'] and f['parental_access'], np.array(bb_response.json()['relationships'], dtype=dict)))

        auth_mask = np.vectorize(lambda f: f['field_id'] == 3078)

        auth_pickups = np.array(bb_custom_response.json()['custom_fields'], dtype=dict)[auth_mask(bb_custom_response.json()['custom_fields'])]

        visit_mask = np.vectorize(lambda f: f['field_id'] == 3098)

        lunch_visitors = np.array(bb_custom_response.json()['custom_fields'], dtype=dict)[visit_mask(bb_custom_response.json()['custom_fields'])]

        at_now = list(filter(lambda f: (parser.parse(f['start_time'], tzinfos=None).isoformat() < datetime.now().isoformat())
                            and (parser.parse(f['end_time'], tzinfos=None).isoformat() > datetime.now().isoformat()), bb_schedule_response.json()['value']))
    except httpx.ReadTimeout:
        raise HTTPException(status_code=503, detail="server timeout, please refresh the page and contact helpdesk for futher support")
    return JSONResponse({'student': bb_response.json(), 'pickups': auth_pickups.tolist(), 'visitors': lunch_visitors.tolist(), 'schedule': bb_schedule_response.json()['value'], 'At now': at_now})


@router.get('/students', name='get_students')
async def getStudents(user=Security(get_current_user)):
    buffer: list = []
    student_role_id = 24395
    list_id = 173010
    page_limit = 1000
    i: int = 0
    
    while len(buffer) >= (i * page_limit):
        i += 1
        temp = (await make_bb_sys_get_call(user, f'https://api.sky.blackbaud.com/school/v1/lists/advanced/{list_id}?page={i}&page_size={page_limit}')).json()['results']['rows']
        buffer.extend(temp)
    
    buffer = [val['columns'] for val in buffer]
    out: np.array = np.array([], dtype=dict)
    for val in buffer:
        new_val = dict()
        for v in val:
            new_val[v['name']] = v['value']
        out = np.append(out, new_val)

    print(out)
    df = pd.DataFrame(out)
    return JSONResponse(json.loads(json.dumps(list(out))))


@router.get('/search/byname', name='name_search')
async def searchByName(request: Request, user=Security(get_current_user)):
    return JSONResponse({'name': 'Tanner'})


@router.get('/grades', name='get_env_grades')
async def getGrades(request: Request, user=Security(get_current_user)):
    return


@router.get('/section/{id}/teacher', name='get_section_teacher')
async def getTeacherExtensionBySection(id: int, user=Security(get_current_user)):
    date = datetime.now().isoformat()
    bb_headers = {
        'Cache-Control': 'no-cache',
        'Bb-Api-Subscription-Key': os.getenv('bb_subscription'),
        'Authorization': user['access']
    }
    async with httpx.AsyncClient() as client:
        bb_section_response = await make_bb_get_call(user, f'https://api.sky.blackbaud.com/school/v1/schedules/meetings?start_date={date}&end_date={date}&section_ids={id}', bb_headers, 0, client=client)
        
        try:
            teacher_id: int = list(filter(lambda f: f['head'], bb_section_response.json()['value'][0]['teachers']))[0]['id']
            teacher_ext = await _fetch_work_extension(teacher_id, client, user)
        except (IndexError, KeyError):
            teacher_id = -1
            teacher_ext = ''
    return {'teacher_id': teacher_id, 'teacher_ext': teacher_ext}


async def _fetch_work_extension(id: int, client: httpx.AsyncClient, user: dict) -> str:
    bb_response = await make_bb_get_call(user, bb_url=f'https://api.sky.blackbaud.com/school/v1/users/{id}/phones', num_attempts=0, client=client)
    try:
        phone = list(filter(lambda f: f['links'][0]['id'] == int(os.getenv('work_phone_id')), bb_response.json()['value']))[0]
        ext: str = re.sub(r'ext. ', '', re.search(r'ext. [0-9]*', phone['number']).group())
        return ext
    except IndexError:
        return ''


@router.get('/user/{id}/phones/work/extension', name='get_user_work_phone')
async def getUserWorkExtension(id: int, user=Security(get_current_user)):
    async with httpx.AsyncClient() as client:
        return await _fetch_work_extension(id, client, user)
