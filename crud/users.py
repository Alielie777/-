import secrets
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.users import User, UserToken
from schemas.users import UserRequest
from utils import security

# 根据用户名查询数据库
async def get_user_by_username(db: AsyncSession , username: str):
    statement = select(User).where(User.username == username)
    result = await db.execute(statement)
    return result.scalar_one_or_none()

# 创建用户
async def create_user(db: AsyncSession, user_data: UserRequest):
    # 先对密码加密处理
    hash_pwd = security.get_hash_password(user_data.password)
    user = User(username=user_data.username, password=hash_pwd )
    db.add(user)
    # 先写入当前事务以获得自增ID；由 create_token 统一提交注册和 token。
    await db.flush()
    await db.refresh(user)
    return user

# 生成 Token
async def create_token(db: AsyncSession, user_id: int):
    """为用户创建或轮换唯一 token，7 天后过期。"""
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(days=7)

    try:
        # 锁住用户行，避免并发请求同时为同一用户插入多条 token。
        user_result = await db.execute(
            select(User.id).where(User.id == user_id).with_for_update()
        )
        if user_result.scalar_one_or_none() is None:
            raise ValueError(f"用户不存在: {user_id}")

        result = await db.execute(
            select(UserToken)
            .where(UserToken.user_id == user_id)
            .order_by(UserToken.id.desc())
        )
        existing_tokens = result.scalars().all()

        if existing_tokens:
            user_token = existing_tokens[0]
            # 清理旧版本代码可能留下的重复记录，避免旧 token 继续有效。
            for duplicate in existing_tokens[1:]:
                await db.delete(duplicate)
            user_token.token = token
            user_token.expires_at = expires_at
        else:
            db.add(
                UserToken(
                    user_id=user_id,
                    token=token,
                    expires_at=expires_at,
                )
            )

        await db.commit()
        return token
    except Exception:
        await db.rollback()
        raise
