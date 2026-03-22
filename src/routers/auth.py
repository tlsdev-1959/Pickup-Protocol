# routers/auth.py
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from authlib.integrations.starlette_client import OAuth
import httpx
import os
import numpy as np
from datetime import datetime, timezone, timedelta
import jwt


router = APIRouter()
oauth = OAuth()
oauth.register( # Register the OAuth Client application
    name="blackbaud",
    client_id=os.getenv('bb_client_id'), client_secret=os.getenv('bb_client_secret'),
    authorize_url="https://app.blackbaud.com/oauth/authorize",
    access_token_url="https://oauth2.sky.blackbaud.com/token",
)

## Helper Functions
# Input: List of JSON objects containing an object for each role the user has
# Output: A boolean value is returned; if the user has access based on the roles input,
#         True will be returned; otherwise False
# Implementation: This function is implemented by utilizing the builtin filter() function
#                 on the list of roles in the input to reduce the list to contain only those roles
#                 with the matching role_id required. Once this list is shortedn, the cardinality
#                 of the list is then measured to determine if the roles that grant access are in the
#                 user input roles.
# Time Complexity: O(n) | n is the number of roles the user has assigned
# Space Complexity: O(1)
async def checkAccess(roles) -> bool:
    n: int = len(list(filter(lambda r: r['id'] == 74122, roles)))
    print(n)
    return n > 0
# END checkAccess


## Auth Routes


@router.get('/', name='auth')
async def authorize(request: Request):
    redirect = request.url_for('auth_callback') # set the redirect url to be the callback end-point
    return await oauth.blackbaud.authorize_redirect(request, redirect)

@router.get('/callback', name='auth_callback')
async def callback(request: Request):
    token = await oauth.blackbaud.authorize_access_token(request) # get the oauth access token
    access: str = token['token_type'] + ' ' + token['access_token'] # format the token with both type and access token


    session = {
        'email': token['email'],
        'access_token': access,
        'expires': datetime.now(timezone.utc) + timedelta(seconds=token['expires_in'])
    }

    
    
   # webToken = jwt.encode(session, os.getenv())

  #  return {'access_token': access,
    #         'web_token': session}



    headers = {
        'Cache-Control': 'no-cache',
        'Bb-Api-Subscription-Key': 'da04e1938daa4ed28e9fd5a0e29f1cd9',
        'Authorization': access
    }
    url = 'https://api.sky.blackbaud.com/school/v1/users/me'
    print('[*] Response: ')
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)


    user = response.json()

    id = user['id']

    url = f'https://api.sky.blackbaud.com/school/v1/users/{id}'

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)

    url = f'https:{response.json()['profile_pictures']['large_filename_url']}'

    if user['is_faculty']:
        print(f'[*] User Log: User {user['id']} is a faculty authorizing') # check if user logging in is faculty
    else:
        return None

    roles = list(user['roles']) # get the user's roles 

    if await checkAccess(roles):
        print('[*] Successful authentication and authorization')
        return HTMLResponse(f'<h1>Access Granted, {user['first_name']}</h1>')
    else:
        return HTMLResponse('<h1>Access Denied</h1>')
   # return filter(lambda x: x['id'] == 24392, user['roles'])