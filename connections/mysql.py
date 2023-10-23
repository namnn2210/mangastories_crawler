from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from configs.config import DBUSERNAME, DBPASSWORD, DBHOST, DBPORT, DBNAME


def get_connection():
    return create_engine(
        url=f"mysql+pymysql://{DBUSERNAME}:{DBPASSWORD}@{DBHOST}:{DBPORT}/{DBNAME}"
    )


def mysql_connect():
    engine = get_connection()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    return db
