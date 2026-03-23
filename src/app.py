from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from authlib.integrations.starlette_client import OAuth
import uvicorn
from routers import public, private, auth
import os


#from routers import public, protected, auth


app = FastAPI() # create instance of the web server
app.add_middleware(SessionMiddleware, secret_key=os.getenv('session_secret'))
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

app.include_router(public.router)
app.include_router(private.router, prefix="/app")
app.include_router(auth.router, prefix="/auth")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "errorCode": exc.status_code,
            "errorMsg": exc.detail
        },
        status_code=exc.status_code
    )

for route in app.routes:
    print(f"PATH: {route.path!r:40} NAME: {getattr(route, 'name', None)!r}")

if __name__ == "__main__":
    # Note: Use a string "main:app" if you want to use 'reload=True'
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)