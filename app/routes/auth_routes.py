from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import Session

from app.models import User
from app.database import SessionLocal
from app.auth import hash_password, verify_password

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")

SESSION_MAX_AGE_SECONDS = 60 * 60


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/")
def home(request: Request):
    if request.cookies.get("user"):
        return RedirectResponse("/dashboard")

    return RedirectResponse("/login")


@router.get("/register")
def register_page(request: Request):
    if request.cookies.get("user"):
        return RedirectResponse("/dashboard")

    return templates.TemplateResponse(
        request,
        "register.html",
        {
            "request": request,
            "show_nav": False,
            "error": request.query_params.get("error")
        }
    )


@router.post("/register")
def register(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    existing = db.query(User).filter(User.username == username).first()

    if existing:
        return RedirectResponse("/register?error=user_exists", status_code=302)

    user = User(
        username=username,
        password=hash_password(password)
    )

    db.add(user)
    db.commit()

    return RedirectResponse("/login", status_code=302)


@router.get("/login")
def login_page(request: Request):
    if request.cookies.get("user"):
        return RedirectResponse("/dashboard")

    return templates.TemplateResponse(
        request,
        "login.html",
        {
            "request": request,
            "show_nav": False
        }
    )


@router.post("/login")
def login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()

    if not user:
        return RedirectResponse("/login", status_code=302)

    if not verify_password(password, user.password):
        return RedirectResponse("/login", status_code=302)

    response = RedirectResponse("/dashboard", status_code=302)

    response.set_cookie(
        key="user",
        value=username,
        max_age=SESSION_MAX_AGE_SECONDS,
        httponly=True,
        samesite="lax"
    )

    return response


@router.get("/logout")
def logout():
    response = RedirectResponse("/login", status_code=302)

    response.delete_cookie("user")

    return response
