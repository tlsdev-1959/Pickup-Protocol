from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
import uvicorn
from routers import public, private, auth

#from routers import public, protected, auth

jwt: str = 'Cxl57Cp0MCXWnF/4lNj8D4qnADuJlEZ7vkvEq3ZglAod7PIToiYFIEGk4izVCAqILfO11JuOBP9YYYBBw2YT8A=='

app = FastAPI() # create instance of the web server
app.add_middleware(SessionMiddleware, jwt)

templates = Jinja2Templates(directory="../templates")

app.include_router(public.router)
app.include_router(private.router, prefix="/app")
app.include_router(auth.router, prefix="/auth")


if __name__ == "__main__":
    # Note: Use a string "main:app" if you want to use 'reload=True'
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)