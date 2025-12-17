"""
verify that our harbor s3 credentials have the right access,
but not more.

Should have full access to the registry bucket,
but no access to other buckets or bucket creation.

# TODO: make the region a parameter
"""

import time
from contextlib import contextmanager
from pathlib import Path

import boto3
import pytest
import yaml
from boto3.exceptions import Boto3Error
from botocore.exceptions import ClientError

repo = Path(__file__).parents[3]

name = "bids-ovh"
registry_bucket_name = f"mybinder-registry-{name}"
private_bucket_name = "mybinder-2i2c-tf-state"
secret_config_path = repo / "secrets/config" / f"{name}.yaml"

with secret_config_path.open() as f:
    secret_config = yaml.safe_load(f)
    harbor_s3 = secret_config["harbor"]["persistence"]["imageChartStorage"]["s3"]
    access_key = harbor_s3["accesskey"]
    secret_key = harbor_s3["secretkey"]


@pytest.fixture
def s3():
    return boto3.Session(
        region_name="us-east-va",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    ).client("s3", endpoint_url="https://s3.us-east-va.io.cloud.ovh.us")


@contextmanager
def s3_raises(msg):
    with pytest.raises((ClientError, Boto3Error), match=msg):
        yield


def test_create_bucket(s3):
    bucket_name = f"test-{name}-{int(time.time())}"
    try:
        s3.create_bucket(Bucket=bucket_name)
    except ClientError as e:
        assert e.response["Error"]["Code"] == "AccessDenied"
    else:
        s3.delete_bucket(Bucket=bucket_name)
        pytest.fail(f"Harbor was able to create bucket {bucket_name}")


def test_access_registry_bucket(s3, tmp_path):
    bucket = registry_bucket_name
    s3.list_objects(Bucket=bucket, MaxKeys=2)
    p = tmp_path / f"testfile.{int(time.time())}"
    p.write_text("test")
    key = f"test/{p.name}"
    s3.upload_file(Bucket=bucket, Key=key, Filename=str(p))
    s3.get_object(Bucket=bucket, Key=key)
    s3.delete_object(Bucket=bucket, Key=key)


def test_access_other_bucket(s3, tmp_path):
    bucket = private_bucket_name
    with s3_raises("AccessDenied"):
        s3.list_objects(Bucket=bucket)
    p = tmp_path / f"testfile.{int(time.time())}"
    p.write_text("test")
    key = f"test/{p.name}"
    with s3_raises("AccessDenied"):
        s3.upload_file(Bucket=bucket, Key=key, Filename=str(p))
