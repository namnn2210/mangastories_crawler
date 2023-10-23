import boto3
import botocore
from configs.config import S3_AWS_ACCESS_KEY_ID, S3_AWS_SECRET_ACCESS_KEY, S3_ENDPOINT_URL, S3_REGION_NAME


def s3_connect():
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
