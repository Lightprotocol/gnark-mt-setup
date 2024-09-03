#!/usr/bin/env python3
import sys
import boto3
import subprocess
import os
from botocore.exceptions import ClientError
from concurrent.futures import ThreadPoolExecutor, as_completed
import shutil

def list_bucket_objects(bucket_name, prefix=''):
    s3 = boto3.client('s3', region_name='eu-central-1')
    try:
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        return [obj['Key'] for obj in response.get('Contents', [])]
    except ClientError as e:
        print(f"Error listing bucket objects: {e}")
        return []

def download_file(bucket_name, object_key, local_path):
    # Ensure the directory exists
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    
    s3 = boto3.client('s3', region_name='eu-central-1')
    try:
        s3.download_file(bucket_name, object_key, local_path)
        return True
    except ClientError as e:
        print(f"Error downloading file: {e}")
        return False

def verify_ph2_files(out_file, initial_contribution):
    semaphore_mtb_setup = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'semaphore-mtb-setup', 'semaphore-mtb-setup')
    if not os.path.exists(semaphore_mtb_setup):
        raise FileNotFoundError(f"semaphore-mtb-setup not found at {semaphore_mtb_setup}")
    try:
        result = subprocess.run([semaphore_mtb_setup, 'p2v', out_file, initial_contribution], capture_output=True, text=True, timeout=300)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Verification timed out after 5 minutes"

def extract_name_and_number(filename):
    parts = filename.split('_')
    return parts[-3], int(parts[-1].split('.')[0])

def download_file_worker(bucket_name, file, subfolder):
    local_path = os.path.join(subfolder, file.split('/')[-1])
    return f"{'Downloaded' if download_file(bucket_name, file, local_path) else 'Failed to download'} {file} to {local_path}"

def download_txt_file_worker(bucket_name, file, subfolder):
    local_path = os.path.join(subfolder, file.split('/')[-1])
    return f"{'Downloaded' if download_file(bucket_name, file, local_path) else 'Failed to download'} {file} to {local_path}"

def verify_contribution(contributions_dir, verify_logs_dir, subdir, file):
    file_path = os.path.join(contributions_dir, subdir, file)
    name, number = extract_name_and_number(file)
    
    if number == 0:
        return
    
    log_file = os.path.join(verify_logs_dir, f"{number:04d}.txt")
    
    initial_contribution = os.path.join(contributions_dir, "0000_swen", file.replace(f"{name}_contribution_{number}", "swen_contribution_0"))

    success, stdout, stderr = verify_ph2_files(file_path, initial_contribution)
    result_msg = f"Verification of {file_path}: {'Success' if success else 'Failed'}"
    
    with open(log_file, 'a') as f:
        f.write(f"{result_msg}\n{'Output:' if success else 'Error:'}\n{stdout if success else stderr}\n\n")
    
    if success: 
        return f"Verified {number:04d} {name}"
    else:
        return f"Verification failed for {file_path}"

def main(bucket_name, local=False):
    contributions_dir = "./contributions/"
    verify_logs_dir = "./verify_logs/"
    hashes_dir = os.path.join(contributions_dir, "hashes")
    
    if os.path.exists(verify_logs_dir):
        shutil.rmtree(verify_logs_dir)
    os.makedirs(verify_logs_dir, exist_ok=True)
    os.makedirs(contributions_dir, exist_ok=True)
    os.makedirs(hashes_dir, exist_ok=True)

    if not local:
        ph2_files = sorted([obj for obj in list_bucket_objects(bucket_name) if obj.endswith('.ph2')])
        txt_files = sorted([obj for obj in list_bucket_objects(bucket_name) if obj.endswith('.txt')])
        
        new_ph2_files = [file for file in ph2_files if not os.path.exists(os.path.join(contributions_dir, f"{extract_name_and_number(file)[1]:04d}_{extract_name_and_number(file)[0]}", file.split('/')[-1]))]
        new_txt_files = [file for file in txt_files if not os.path.exists(os.path.join(hashes_dir, file.split('/')[-1]))]
        
        print("AWS All PH2 files:", len(ph2_files))
        print("AWS New PH2 files:", len(new_ph2_files))
        print("AWS All TXT files:", len(txt_files))
        print("AWS New TXT files:", len(new_txt_files))

        with ThreadPoolExecutor(max_workers=10) as executor:
            download_tasks = [executor.submit(download_file_worker, bucket_name, file, os.path.join(contributions_dir, f"{extract_name_and_number(file)[1]:04d}_{extract_name_and_number(file)[0]}")) for file in new_ph2_files]
            download_txt_tasks = [executor.submit(download_txt_file_worker, bucket_name, file, hashes_dir) for file in new_txt_files]
            
            for future in as_completed(download_tasks + download_txt_tasks):
                print(future.result())

    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        verify_tasks = [executor.submit(verify_contribution, contributions_dir, verify_logs_dir, subdir, file) 
                        for subdir in sorted(os.listdir(contributions_dir)) 
                        if os.path.isdir(os.path.join(contributions_dir, subdir)) 
                        for file in sorted(os.listdir(os.path.join(contributions_dir, subdir))) 
                        if file.endswith('.ph2')]
        
        for future in as_completed(verify_tasks):
            try:
                result = future.result()
                if result:
                    print(result)
            except Exception as e:
                print(f"Error: {str(e)}")
                sys.exit(1)

    if any(future.exception() is not None for future in verify_tasks):
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python3 ./coordinator/verify_contributions.py <bucket_name> [--local]")
        sys.exit(1)
    
    bucket_name = sys.argv[1]
    local_flag = '--local' in sys.argv
    main(bucket_name, local_flag)
