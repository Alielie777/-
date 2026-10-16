from passlib.context import CryptContext

# 密码加密上下文
pwdContext = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 密码加密
def get_hash_password(password: str):
    return pwdContext.hash(password)