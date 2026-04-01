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

router = APIRouter()
templates = Jinja2Templates(directory='templates')

async def get_current_user(session: str = Cookie(None)):
    print('[*] Encrypted Cookie: ', session)
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(session, os.getenv('session_secret'), algorithms=["HS384"])
        return payload
    except ExpiredSignatureError:
        print('[*] Cookie needs to be refreshed')
        raise HTTPException(status_code=504)
    except JWTError:
        raise HTTPException(status_code=401)
    
async def make_bb_get_call(actor: dict, bb_url: str, bb_headers: dict, num_attempts: int = 0, client: httpx.AsyncClient = httpx.AsyncClient()):
    try:
        async with httpx.AsyncClient() as client:
            bb_response = await client.get(url=bb_url, headers=bb_headers)
        print(bb_response)
        #print(await auth.refresh_bb(actor['refresh']))
        return bb_response
    except httpx.ReadTimeout:
        if num_attempts > 3:
            raise HTTPException(status_code=503)
        else:
            return make_bb_get_call(actor, bb_url, bb_headers, num_attempts + 1)
        
async def make_bucket_of_bb_get_call(actor: dict, url_bucket: list, bb_headers: dict, num_attempts: int = 0, client: httpx.AsyncClient = httpx.AsyncClient()):
    try:
        async with httpx.AsyncClient() as client:
            tasks = [await client.get(url=url, headers=bb_headers) for url in url_bucket]
            return asyncio.gather
            #bb_response = await client.get(url=bb_url, headers=bb_headers)
        print(bb_response)
        #print(await auth.refresh_bb(actor['refresh']))
        return bb_response
    except httpx.ReadTimeout:
        if num_attempts > 3:
            raise HTTPException(status_code=503)
        else:
            return make_bucket_of_bb_get_call(actor, url_bucket, bb_headers, num_attempts + 1)
    #except httpx.:
    #    refreshed = auth.refresh_bb(actor['refresh'])
    #    actor['access'] = refreshed['access']
    #    actor['refresh'] = refreshed['refresh']
    #    actor['exp'] = datetime.now(int((datetime.now(timezone.utc) + timedelta(seconds=auth.session_exp)).timestamp()))

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
    bb_url: str = f'https://api.sky.blackbaud.com/school/v1/users/{user['user']}'
    bb_headers = {
        'Cache-Control': 'no-cache',
        'Bb-Api-Subscription-Key': os.getenv('bb_subscription'),
        'Authorization': user['access']
    }
    bb_response = await make_bb_get_call(user, bb_url, bb_headers)
    out_url = 'https:'+bb_response.json()['profile_pictures']['thumb_filename_url']
    return JSONResponse({"url": out_url})


## Student API ##

@router.get('/student', name='get_student_by_user_id')
async def studentById(request: Request, id: int, user=Security(get_current_user)):
    bb_url: str = f'https://api.sky.blackbaud.com/school/v1/users/extended/{id}'
    bb_custom_url: str = f'https://api.sky.blackbaud.com/school/v1/users/{id}/customfields'
    bb_schedule_url: str = f'https://api.sky.blackbaud.com/school/v1/schedules/{id}/meetings?start_date={datetime.now().date()}&end_date={datetime.now().date()}'
    bb_headers = {
        'Cache-Control': 'no-cache',
        'Bb-Api-Subscription-Key': os.getenv('bb_subscription'),
        'Authorization': user['access']
    }
    #print(await make_bucket_of_bb_get_call(user, [bb_url, bb_custom_url, bb_schedule_url], bb_headers))
    #print('[!] Schedule: ', bb_schedule_url)
    #print('[*] URL: ', bb_custom_url)
    try:
        bb_response = await make_bb_get_call(user, bb_url, bb_headers)
        bb_custom_response = await make_bb_get_call(user, bb_custom_url, bb_headers)
        bb_schedule_response = await make_bb_get_call(user, bb_schedule_url, bb_headers)
        auth_pickups = [v['text_value'] for v in list(filter(lambda f: f['field_id'] == 3078, bb_custom_response.json()['custom_fields']))]
        lunch_visitors = [v['text_value'] for v in list(filter(lambda f: f['field_id'] == 3098, bb_custom_response.json()['custom_fields']))] 
        at_now = list(filter(lambda f: (parser.parse(f['start_time'], tzinfos=None).isoformat() < datetime.now().isoformat())
                            and (parser.parse(f['end_time'], tzinfos=None).isoformat() > datetime.now().isoformat()), bb_schedule_response.json()['value']))
        if not len(at_now):
            at_now = bb_schedule_response.json()['value'][0]
        else:
            at_now = at_now[0]
    except httpx.ReadTimeout:
        raise HTTPException(status_code=503, detail="server timeout, please refresh the page and contact helpdesk for futher support")
    

    ext = await getTeacherExtensionBySection(request, at_now['section_id'], user)
    
    return JSONResponse({'student': bb_response.json(), 'pickups': auth_pickups, 'visitors': lunch_visitors, 'schedule': bb_schedule_response.json()['value'], 'At now': at_now, 'teacher_ext': ext})


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
    out :np.array = np.array([], dtype=dict)
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


@router.get('/section/teacher', name='get_section_teacher')
async def getTeacherExtensionBySection(request: Request, id: int, user=Security(get_current_user)):
    date = datetime.now().isoformat()
    bb_section_response = await make_bb_sys_get_call(user, f'https://api.sky.blackbaud.com/school/v1/schedules/meetings?start_date={date}&end_date={date}&section_ids={id}')
    teacher_id: int = list(filter(lambda f: f['head'], bb_section_response.json()['value'][0]['teachers']))[0]['id']
    teacher_ext = await getUserWorkExtension(request, teacher_id, user)
    return teacher_ext


@router.get('/user/phones/work/extension', name='get_user_work_phone')
async def getUserWorkExtension(request: Request, id: int, user=Security(get_current_user)):
    bb_response = await make_bb_sys_get_call(user, f'https://api.sky.blackbaud.com/school/v1/users/{id}/phones')

    phone = list(filter(lambda f: f['links'][0]['id'] == int(os.getenv('work_phone_id')), bb_response.json()['value']))[0]
    
    ext: int = re.sub(r'ext. ', '', re.search(r'ext. [0-9]*', phone['number']).group())
    
    return ext
