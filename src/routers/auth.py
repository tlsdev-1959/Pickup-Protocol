# routers/auth.py
from fastapi import APIRouter, Request, Depends, HTTPException, Cookie
from fastapi.responses import RedirectResponse, HTMLResponse
from authlib.integrations.starlette_client import OAuth
import httpx
import os
import numpy as np
from datetime import datetime, timezone, timedelta
from jose import jwt, JWTError
from objects import user, role


router = APIRouter()
oauth = OAuth()
oauth.register( # Register the OAuth Client application
    name="blackbaud",
    client_id=os.getenv('bb_client_id'), client_secret=os.getenv('bb_client_secret'),
    authorize_url="https://app.blackbaud.com/oauth/authorize",
    access_token_url="https://oauth2.sky.blackbaud.com/token",
)





## Auth Routes


@router.get('/login', name='auth')
async def authorize(request: Request):
    redirect = request.url_for('auth_callback') # set the redirect url to be the callback end-point
    return await oauth.blackbaud.authorize_redirect(request, redirect)

@router.get('/callback', name='auth_callback')
async def callback(request: Request):
    try:
        token = await oauth.blackbaud.authorize_access_token(request) # get the oauth access token
        access: str = token['token_type'] + ' ' + token['access_token'] # format the token with both type and access token


        bb_headers = {
            'Cache-Control': 'no-cache',
            'Bb-Api-Subscription-Key': 'da04e1938daa4ed28e9fd5a0e29f1cd9',
            'Authorization': access
        }

        # Make request to get user information
        user_url = 'https://api.sky.blackbaud.com/school/v1/users/me'
        async with httpx.AsyncClient() as client:
            api_response = await client.get(url=user_url, headers=bb_headers)

        appUser = user.User(api_response.json()) # create appUser object

        if appUser.hasAccess:
            session = {
            'user': appUser.id,
            'preferred': appUser.preferred,
            'access': access,
            'refresh': token['refresh_token'],
            'exp': int((datetime.now(timezone.utc) + timedelta(seconds=3600)).timestamp())
            }
            session_jwt = jwt.encode(session, os.getenv('session_secret'), algorithm='HS256')
            finalize_url = str(request.url_for('finalize')) + f"?token={session_jwt}"
            return RedirectResponse(url=finalize_url, status_code=303)
        else:
            response = RedirectResponse(url=str(request.url_for('access_denied')), status_code= 302)
            return response
    except Exception as e:
        import traceback
        print("CALLBACK CRASHED:", traceback.format_exc())
        raise

@router.get('/finalize', name='finalize')
async def finalize(request: Request, token: str):
    print("FINALIZE HIT, token:", token)
    redirect = RedirectResponse(url=str(request.url_for('home')), status_code=303)
    redirect.set_cookie(key="session", value=token, httponly=True, path="/")
    print("FINALIZE HEADERS:", dict(redirect.headers))
    return redirect

@router.get("/logout", name="logout")
async def logout(request: Request):
    response = RedirectResponse(url=str(request.url_for('index')), status_code=303)
    response.delete_cookie(key="session", httponly=True, path="/")
    print('[*] Logout Request: ', request.cookies)
    return response
