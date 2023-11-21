from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from configs.config import DBUSERNAME, DBPASSWORD, DBHOST, DBPORT, DBNAME, S3_AWS_ACCESS_KEY_ID, S3_AWS_SECRET_ACCESS_KEY, S3_ENDPOINT_URL, S3_REGION_NAME
from rq import Queue
from .redis_cache import RedisCache

import boto3
import botocore
import pymongo


class Connection():

    def get_connection(self, db_name=DBNAME):
        return create_engine(
            url=f"mysql+pymysql://{DBUSERNAME}:{DBPASSWORD}@{DBHOST}:{DBPORT}/{db_name}"
        )

    def mysql_connect(self, db_name=DBNAME):
        engine = self.get_connection(db_name)
        SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        return db

    def mongo_connect(self):
        client = pymongo.MongoClient("mongodb://localhost:27018/")
        return client["mangamonster"]

    def redis_connect(self, db=2, queue_name=''):
        redis_cache = RedisCache(db=db)
        return Queue(queue_name, connection=redis_cache.get_redis(), default_timeout=3600)

    def s3_connect(self):
        session = boto3.session.Session()
        client = session.client('s3',
                                endpoint_url=S3_ENDPOINT_URL,
                                # Find your endpoint in the control panel, under Settings. Prepend "https://".
                                config=botocore.config.Config(
                                    s3={'addressing_style': 'virtual'}),
                                # Configures to use subdomain/virtual calling format.
                                # Use the region in your endpoint.
                                region_name=S3_REGION_NAME,
                                aws_access_key_id=S3_AWS_ACCESS_KEY_ID,
                                # Access key pair. You can create access key pairs using the control panel or API.
                                aws_secret_access_key=S3_AWS_SECRET_ACCESS_KEY)  # Secret access key defined through an environment variable.

        return client
