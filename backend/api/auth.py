# auth.py
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from model.users import UserModel, UserPublic
from db import get_db
from core.api_result import success, error, ApiResponse
from core.auth import get_current_user
from utils.security import hash_password, verify_password, generate_token
from utils.wechat import exchange_code_for_openid, fetch_wechat_userinfo

router = APIRouter(prefix="/auth", tags=["auth"])

TOKEN_VALID_DAYS = 30


class AuthData(BaseModel):
    token: str
    user: UserPublic


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=20)
    password: str = Field(..., min_length=3, max_length=100)


class LoginRequest(BaseModel):
    username: str
    password: str


class WechatLoginRequest(BaseModel):
    code: str


def _issue_token(db: Session, user: UserModel) -> str:
    token = generate_token()
    UserModel.update(
        db,
        {
            "id": user.id,
            "token": token,
            "token_expires_at": datetime.now() + timedelta(days=TOKEN_VALID_DAYS),
        },
    )
    return token


@router.post("/register", response_model=ApiResponse[AuthData], summary="账号密码注册")
async def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = UserModel.select_one_by(db, {"username": payload.username})
    if existing:
        return error("用户名已存在", code=400)

    user_id = UserModel.insert(
        db, {"username": payload.username, "password": hash_password(payload.password)}
    )
    user = UserModel.get_by_id(db, user_id)
    token = _issue_token(db, user)
    return success({"token": token, "user": UserModel.get_by_id(db, user_id)})


@router.post("/login", response_model=ApiResponse[AuthData], summary="账号密码登录")
async def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = UserModel.select_one_by(db, {"username": payload.username})
    if not user or not user.password or not verify_password(payload.password, user.password):
        return error("用户名或密码错误", code=400)

    token = _issue_token(db, user)
    return success({"token": token, "user": UserModel.get_by_id(db, user.id)})


@router.post("/wechat/login", response_model=ApiResponse[AuthData], summary="微信扫码登录")
async def wechat_login(payload: WechatLoginRequest, db: Session = Depends(get_db)):
    try:
        token_data = exchange_code_for_openid(payload.code)
        userinfo = fetch_wechat_userinfo(token_data["access_token"], token_data["openid"])
    except RuntimeError as e:
        return error(str(e))

    openid = token_data["openid"]
    user = UserModel.select_one_by(db, {"wx": openid})
    if not user:
        user_id = UserModel.insert(
            db,
            {
                "wx": openid,
                "nickname": userinfo["nickname"],
                "avatar": userinfo["headimgurl"],
            },
        )
        user = UserModel.get_by_id(db, user_id)
    else:
        UserModel.update(
            db,
            {
                "id": user.id,
                "nickname": userinfo["nickname"],
                "avatar": userinfo["headimgurl"],
            },
        )
        user = UserModel.get_by_id(db, user.id)

    token = _issue_token(db, user)
    return success({"token": token, "user": UserModel.get_by_id(db, user.id)})


@router.get("/me", response_model=ApiResponse[UserPublic], summary="获取当前登录用户")
async def me(current_user: UserModel = Depends(get_current_user)):
    return success(current_user)
