#!/usr/bin/env python3
import sys
import boto3
from botocore.exceptions import ClientError

def create_presigned_url(bucket_name, object_key, expiration, region_name, http_method='GET'):
    s3_client = boto3.client('s3', region_name=region_name)
    try:
        return s3_client.generate_presigned_url(
            'get_object' if http_method == 'GET' else 'put_object',
            Params={'Bucket': bucket_name, 'Key': object_key},
            ExpiresIn=expiration,
            HttpMethod=http_method
        )
    except ClientError as e:
        print(f"Error creating presigned URL: {e}")
        return None

if len(sys.argv) < 7:
    print("Usage: python3 ./coordinator/create-urls.py <bucket_name> <current_user> <last_number> <last_user> <expiration_seconds> <region_name>")
    sys.exit(1)

bucket_name = sys.argv[1]
current_user = sys.argv[2]
last_number = int(sys.argv[3])
last_user = sys.argv[4]
expiration = int(sys.argv[5])
region_name = sys.argv[6]

current_number = last_number + 1


PH2_FILES= [
    "inclusion_26_1",
    "inclusion_26_2",
    "inclusion_26_3",
    "inclusion_26_4",
    "inclusion_26_8",
    "non-inclusion_26_1",
    "non-inclusion_26_2",
    "non-inclusion_26_3",
    "non-inclusion_26_4",
    "non-inclusion_26_8",
    "combined_26_1_1",
    "combined_26_1_2",
    "combined_26_1_4",
    "combined_26_1_8",
    "combined_26_2_1",
    "combined_26_2_2",
    "combined_26_2_4",
    "combined_26_2_8",
    "combined_26_3_1",
    "combined_26_3_2",
    "combined_26_3_4",
    "combined_26_3_8",
    "combined_26_4_1",
    "combined_26_4_2",
    "combined_26_4_4",
    "combined_26_4_8",
    "combined_26_8_1",
    "combined_26_8_2",
    "combined_26_8_4",
    "combined_26_8_8",
]

# Section 1: Command for running from gist
print("Section 1: Command for running from gist")
print(f"curl -sL https://gist.githubusercontent.com/SwenSchaeferjohann/2ff6ee0c88b110dd6260868abefad6ca/raw/980a28326661725803ddc217edd9a3cd8a874903/light-tsc-contribute.sh | bash -s -- {current_number} \"{current_user}\"", end=" ")

urls = []

# Download URLs for last number
for file in PH2_FILES:
    download_file = f"{file}_{last_user}_contribution_{last_number}.ph2"
    url = create_presigned_url(bucket_name, download_file, expiration, region_name)
    print(f"\"{url}\"", end=" ")
    urls.append(url)

# Upload URLs for current number
for file in PH2_FILES:
    upload_file = f"{file}_{current_user}_contribution_{current_number}.ph2"
    url = create_presigned_url(bucket_name, upload_file, expiration, region_name, http_method='PUT')
    print(f"\"{url}\"", end=" ")
    urls.append(url)

# Add URL for contribution file (assuming this is an upload)
contrib_file = f"{current_user}_CONTRIBUTION_{current_number}.txt"
url = create_presigned_url(bucket_name, contrib_file, expiration, region_name, http_method='PUT')
print(f"\"{url}\"")
urls.append(url)

# Section 2: Command for running contribute.sh locally
print("\n\nSection 2: Command for running contribute.sh locally")
print(f"./contribute.sh {current_number} \"{current_user}\" " + " ".join(f"\"{url}\"" for url in urls))