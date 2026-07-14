import secrets
from datetime import datetime, timedelta
from typing import Optional
import bcrypt
from fastapi import Depends, HTTPException, Request
from app.domain.auth.entity import User
from app.domain.auth.repository import IAuthRepository
from app.infrastructure.database.repositories import get_auth_repo

SESSION_COOKIE = "session_token"
SESSION_MAX_AGE = 60 * 60 * 24  # 24시간


class AuthService:
    def __init__(self, repo: IAuthRepository):
        self._repo = repo

    def login(self, username: str, password: str) -> dict:
        user = self._repo.get_user_by_username(username)
        if not user or not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
            raise HTTPException(401, "아이디 또는 비밀번호가 올바르지 않습니다")
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(seconds=SESSION_MAX_AGE)
        self._repo.create_session(user.id, token, expires_at)
        return {"token": token, "username": user.username}

    def logout(self, token: str) -> None:
        if token:
            self._repo.delete_session(token)

    def get_current_user(self, token: str) -> Optional[User]:
        if not token:
            return None
        session = self._repo.get_session(token)
        if not session or session.expires_at < datetime.now():
            return None
        return self._repo.get_user(session.user_id)

    def change_password(self, user_id: int, current_password: str, new_password: str) -> None:
        user = self._repo.get_user(user_id)
        if not user:
            raise HTTPException(404, "사용자를 찾을 수 없습니다")
        if not bcrypt.checkpw(current_password.encode(), user.password_hash.encode()):
            raise HTTPException(400, "현재 비밀번호가 올바르지 않습니다")
        if len(new_password) < 4:
            raise HTTPException(400, "새 비밀번호는 4자 이상이어야 합니다")
        new_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
        self._repo.update_password(user_id, new_hash)


def get_auth_service(repo: IAuthRepository = Depends(get_auth_repo)) -> AuthService:
    return AuthService(repo)


def require_login(request: Request, svc: AuthService = Depends(get_auth_service)) -> User:
    token = request.cookies.get(SESSION_COOKIE)
    user = svc.get_current_user(token)
    if not user:
        raise HTTPException(401, "로그인이 필요합니다")
    return user
