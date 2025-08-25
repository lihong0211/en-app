# user.py
from fastapi import APIRouter, Query, HTTPException, Depends, status
from typing import Optional, List
from sqlalchemy.orm import Session

from users import UserModel, UserOut, UserCreate, UserUpdate
from db import get_db

router = APIRouter(
    prefix="/users", tags=["users"], responses={404: {"description": "Not found"}}
)


@router.get("/", response_model=List[UserOut], summary="获取用户列表")
async def get_users(
    skip: int = Query(0, description="跳过记录数"),
    limit: int = Query(10, description="每页记录数", le=100),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    db: Session = Depends(get_db),
):
    """
    获取用户列表，支持分页和过滤
    """
    criterion = {}
    if is_active is not None:
        criterion["is_active"] = is_active

    users = UserModel.select_by(db, criterion)
    return users[skip : skip + limit]


@router.get("/{user_id}", response_model=UserOut, summary="根据ID获取用户")
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """
    根据用户ID获取单个用户信息
    """
    user = UserModel.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


@router.post(
    "/", response_model=UserOut, status_code=status.HTTP_201_CREATED, summary="创建用户"
)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    创建新用户
    """
    # 检查邮箱是否已存在
    existing_user = UserModel.select_one_by(db, {"email": user.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # 检查用户名是否已存在
    existing_username = UserModel.select_one_by(db, {"username": user.username})
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken"
        )

    # 创建用户
    user_data = user.dict()
    user_id = UserModel.insert(db, user_data)

    # 返回新创建的用户
    return UserModel.get_by_id(db, user_id)


@router.put("/{user_id}", response_model=UserOut, summary="更新用户")
async def update_user(
    user_id: int, user_data: UserUpdate, db: Session = Depends(get_db)
):
    """
    更新用户信息
    """
    # 检查用户是否存在
    existing_user = UserModel.get_by_id(db, user_id)
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    update_dict = user_data.dict(exclude_unset=True)

    # 如果更新邮箱，检查新邮箱是否已被其他用户使用
    if "email" in update_dict and update_dict["email"] != existing_user.email:
        email_exists = UserModel.select_one_by(db, {"email": update_dict["email"]})
        if email_exists and email_exists.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered by another user",
            )

    # 如果更新用户名，检查新用户名是否已被其他用户使用
    if "username" in update_dict and update_dict["username"] != existing_user.username:
        username_exists = UserModel.select_one_by(
            db, {"username": update_dict["username"]}
        )
        if username_exists and username_exists.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken by another user",
            )

    # 更新用户数据
    update_dict["id"] = user_id
    UserModel.update(db, update_dict)

    # 返回更新后的用户
    return UserModel.get_by_id(db, user_id)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除用户")
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    """
    删除用户（软删除）
    """
    # 检查用户是否存在
    existing_user = UserModel.get_by_id(db, user_id)
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # 执行软删除
    UserModel.delete(db, user_id)


@router.patch("/{user_id}/activate", response_model=UserOut, summary="激活/禁用用户")
async def activate_user(user_id: int, is_active: bool, db: Session = Depends(get_db)):
    """
    激活或禁用用户
    """
    # 检查用户是否存在
    existing_user = UserModel.get_by_id(db, user_id)
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # 更新用户激活状态
    update_data = {"id": user_id, "is_active": is_active}
    UserModel.update(db, update_data)

    # 返回更新后的用户
    return UserModel.get_by_id(db, user_id)
