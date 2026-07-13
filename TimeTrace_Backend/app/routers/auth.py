from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import secrets
import requests

from app.db import get_db
from app.db.models import User
from app.core.config import settings

router = APIRouter()

# 配置JWT
SECRET_KEY = "your-secret-key-change-this-in-production"  # 使用固定的密钥，生产环境中应从环境变量读取
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7天

# 配置密码哈希
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 配置OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

from pydantic import BaseModel

class RegisterUser(BaseModel):
    username: str
    email: str
    password: str

class WechatLoginRequest(BaseModel):
    code: str
    nickName: str = ""
    avatarUrl: str = ""

class BindWechatRequest(BaseModel):
    username: str
    password: str
    code: str
    nickName: str = ""
    avatarUrl: str = ""

@router.post("/register", response_model=dict)
def register_user(
    user_data: RegisterUser,
    db: Session = Depends(get_db)
):
    """用户注册"""
    # 检查密码长度
    if len(user_data.password) < 6:
        raise HTTPException(status_code=400, detail="密码长度至少6位")
    
    # 检查用户名是否已存在
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 检查邮箱是否已存在
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="邮箱已存在")
    
    # 创建新用户
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {
        "id": new_user.id,
        "username": new_user.username,
        "email": new_user.email,
        "message": "注册成功"
    }

@router.post("/login", response_model=dict)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """用户登录，获取访问令牌"""
    # 验证用户
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not user.password_hash or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    }

@router.get("/me", response_model=dict)
def read_users_me(current_user: User = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "wechat_avatar": current_user.wechat_avatar,
        "created_at": current_user.created_at
    }


@router.post("/wechat-login", response_model=dict)
def wechat_login(
    login_data: WechatLoginRequest,
    db: Session = Depends(get_db)
):
    """微信小程序登录 - 通过 wx.login() code 换取 JWT token"""
    
    # 1. 调用微信 code2Session 接口换取 openid
    wechat_url = "https://api.weixin.qq.com/sns/jscode2session"
    params = {
        "appid": settings.WECHAT_APPID,
        "secret": settings.WECHAT_SECRET,
        "js_code": login_data.code,
        "grant_type": "authorization_code"
    }
    
    try:
        resp = requests.get(wechat_url, params=params, timeout=10)
        resp_data = resp.json()
    except Exception:
        raise HTTPException(status_code=500, detail="微信服务器通信失败")
    
    if "errcode" in resp_data and resp_data["errcode"] != 0:
        raise HTTPException(status_code=400, detail=f"微信登录失败: {resp_data.get('errmsg', '未知错误')}")
    
    openid = resp_data.get("openid")
    unionid = resp_data.get("unionid")
    
    if not openid:
        raise HTTPException(status_code=400, detail="获取微信openid失败")
    
    # 2. 查找或创建用户
    user = db.query(User).filter(User.wechat_openid == openid).first()
    
    if not user:
        # 创建新用户（微信小程序无需邮箱和密码）
        username = login_data.nickName if login_data.nickName else f"微信用户{openid[-6:]}"
        # 确保用户名唯一
        base_username = username
        counter = 1
        while db.query(User).filter(User.username == username).first():
            username = f"{base_username}{counter}"
            counter += 1
        
        user = User(
            username=username,
            email=None,
            password_hash=None,
            wechat_openid=openid,
            wechat_unionid=unionid,
            wechat_avatar=login_data.avatarUrl
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # 更新用户头像
        if login_data.avatarUrl:
            user.wechat_avatar = login_data.avatarUrl
        db.commit()
        db.refresh(user)
    
    # 3. 生成 JWT token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "wechat_avatar": user.wechat_avatar
        }
    }


@router.post("/bind-wechat", response_model=dict)
def bind_wechat(
    bind_data: BindWechatRequest,
    db: Session = Depends(get_db)
):
    """将已有邮箱账号绑定微信小程序 - 先验证密码，再关联 openid"""
    
    # 1. 验证邮箱账号和密码
    user = db.query(User).filter(User.username == bind_data.username).first()
    if not user or not user.password_hash or not verify_password(bind_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    # 2. 获取微信 openid
    wechat_url = "https://api.weixin.qq.com/sns/jscode2session"
    params = {
        "appid": settings.WECHAT_APPID,
        "secret": settings.WECHAT_SECRET,
        "js_code": bind_data.code,
        "grant_type": "authorization_code"
    }
    
    try:
        resp = requests.get(wechat_url, params=params, timeout=10)
        resp_data = resp.json()
    except Exception:
        raise HTTPException(status_code=500, detail="微信服务器通信失败")
    
    if "errcode" in resp_data and resp_data["errcode"] != 0:
        raise HTTPException(status_code=400, detail=f"微信登录失败: {resp_data.get('errmsg', '未知错误')}")
    
    openid = resp_data.get("openid")
    if not openid:
        raise HTTPException(status_code=400, detail="获取微信openid失败")
    
    # 3. 检查 openid 是否已被其他用户绑定
    existing = db.query(User).filter(User.wechat_openid == openid).first()
    if existing and existing.id != user.id:
        raise HTTPException(status_code=400, detail="该微信已绑定其他账号")
    
    # 4. 绑定微信信息
    user.wechat_openid = openid
    user.wechat_unionid = resp_data.get("unionid")
    if bind_data.avatarUrl:
        user.wechat_avatar = bind_data.avatarUrl
    db.commit()
    db.refresh(user)
    
    # 5. 生成 JWT token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "wechat_avatar": user.wechat_avatar
        },
        "message": "微信绑定成功"
    }
