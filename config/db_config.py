import os

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker,AsyncSession, create_async_engine

# 从环境变量读取数据库连接地址，避免将账号密码提交到仓库。
ASYNC_DB_URI = os.getenv("ASYNC_DB_URI")
if not ASYNC_DB_URI:
    raise RuntimeError("请先设置环境变量 ASYNC_DB_URI")

# 创建异步引擎
engine = create_async_engine(
    ASYNC_DB_URI,
    echo=True,       # 输出SQL日志
    pool_size=10,    # 设置连接池中保持的持久连接数
    max_overflow=20, # 设置连接池允许创建的额外连接数
)

# 创建异步会话工厂
AsyncSession = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# 依赖项，用于获取数据库会话
async def get_db():
    async with AsyncSession(bind=engine) as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
