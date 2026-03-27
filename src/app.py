from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from authlib.integrations.starlette_client import OAuth
import uvicorn
from routers import public, private, auth, api
import os





app = FastAPI() # create instance of the web server

# Add a middleware to handle cross-orgin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # your frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add a middleware to handle the cookies and authenticate requests
app.add_middleware(SessionMiddleware, secret_key=os.getenv('session_secret'))

# Mount the statuc and templates directories
app.mount("/static", StaticFiles(directory="static"), name="static") 
templates = Jinja2Templates(directory="templates") # Mount the directory of templates


# Initialize the routes that the API of the web app can take
app.include_router(public.router)
app.include_router(private.router, prefix="/app")
app.include_router(api.router, prefix='/api')
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

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=80, reload=True)