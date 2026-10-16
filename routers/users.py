'''
用户模块路由
'''
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from config.db_config import get_db
from crud import users
from schemas.users import UserRequest, UserAuthResponse, UserInfoResponse
from utils.response import success_response

router = APIRouter(prefix="/api/user", tags=["user"])

@router.post("/register")
async def register(user_data: UserRequest, db: AsyncSession = Depends(get_db)):
    # 验证用户是否存在
    exist = await users.get_user_by_username(db, user_data.username)
    if exist:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="用户已存在 ")
    # 如果用户不存在，就先创建用户
    user = await users.create_user(db, user_data)
    # 创建完用户紧接着生成token
    token = await users.create_token(db, user.id)

    # return {
    #     "code": "code",
    #     "message": "注册成功",
    #     "data": {
    #         "token": token,
    #         "userInfo": {
    #             "id": user.id,
    #             "username": user.username,
    #             "bio": user.bio,
    #             "avatar": user.avatar
    #         }
    #     }
    # }
    response_data = UserAuthResponse(token=token,userInfo=UserInfoResponse.model_validate(user))
    return success_response(message="注册成功",data=response_data)
