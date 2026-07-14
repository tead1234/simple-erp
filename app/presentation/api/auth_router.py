from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.application.auth_service import (
    AuthService, get_auth_service, require_login, SESSION_COOKIE, SESSION_MAX_AGE,
)
from app.domain.auth.entity import User
from app.infrastructure.database.session import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginIn(BaseModel):
    username: str
    password: str


class ChangePasswordIn(BaseModel):
    current_password: str
    new_password: str


@router.post("/login")
def login(data: LoginIn, response: Response,
          svc: AuthService = Depends(get_auth_service), db: Session = Depends(get_db)):
    result = svc.login(data.username, data.password)
    response.set_cookie(
        SESSION_COOKIE, result["token"], max_age=SESSION_MAX_AGE,
        httponly=True, samesite="lax",
    )
    db.commit()
    return {"username": result["username"]}


@router.post("/logout")
def logout(request: Request, response: Response,
           svc: AuthService = Depends(get_auth_service), db: Session = Depends(get_db),
           user: User = Depends(require_login)):
    svc.logout(request.cookies.get(SESSION_COOKIE))
    response.delete_cookie(SESSION_COOKIE)
    db.commit()
    return {"ok": True}


@router.get("/me")
def me(user: User = Depends(require_login)):
    return {"username": user.username}


@router.post("/change-password")
def change_password(data: ChangePasswordIn, user: User = Depends(require_login),
                     svc: AuthService = Depends(get_auth_service), db: Session = Depends(get_db)):
    svc.change_password(user.id, data.current_password, data.new_password)
    db.commit()
    return {"ok": True}
