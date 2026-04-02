from .base import Base, engine, SessionLocal
from .models import Photo, User, Task

# 创建所有数据库表
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
