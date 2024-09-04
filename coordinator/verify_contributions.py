#!/usr/bin/env python3
import sys
import boto3
import subprocess
import os
import platform
from botocore.exceptions import ClientError
from concurrent.futures import ThreadPoolExecutor, as_completed
import shutil
import tempfile
import traceback

def install_git():
    os_type = platform.system().lower()
    if os_type == "darwin":
        subprocess.run(["brew", "install", "git"], check=True)
    elif os_type == "linux":
        if os.path.exists("/etc/debian_version"):
            subprocess.run(["sudo", "apt", "update"], check=True)
            subprocess.run(["sudo", "apt", "install", "-y", "git"], check=True)
        elif os.path.exists("/etc/redhat-release"):
            subprocess.run(["sudo", "yum", "install", "-y", "git"], check=True)
        else:
            raise OSError("Unsupported Linux distribution. Please install git manually.")
    else:
        raise OSError(f"Unsupported OS: {os_type}")

def install_go():
    os_type = platform.system().lower()
    if os_type == "darwin":
        subprocess.run(["brew", "install", "go"], check=True)
    elif os_type == "linux":
        if os.path.exists("/etc/debian_version"):
            subprocess.run(["sudo", "apt", "update"], check=True)
            subprocess.run(["sudo", "apt", "install", "-y", "golang"], check=True)
        elif os.path.exists("/etc/redhat-release"):
            subprocess.run(["sudo", "yum", "install", "-y", "golang"], check=True)
        else:
            raise OSError("Unsupported Linux distribution. Please install go manually.")
    else:
        raise OSError(f"Unsupported OS: {os_type}")

def setup_semaphore_mtb():
    if not shutil.which("git"):
        print("git not found. Installing git...")
        install_git()

    if not shutil.which("go"):
        print("go not found. Installing go...")
        install_go()

    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Cloning repository to {temp_dir}")
        subprocess.run(["git", "clone", "https://github.com/worldcoin/semaphore-mtb-setup", temp_dir], check=True)
        print("Building semaphore-mtb-setup")
        subprocess.run(["go", "build", "-v"], cwd=temp_dir, check=True)
        print("Copying semaphore-mtb-setup to current directory")
        shutil.copy(os.path.join(temp_dir, "semaphore-mtb-setup"), ".")
    print("semaphore-mtb-setup setup completed")

def verify_ph2_files(out_file, initial_contribution):
    semaphore_mtb_setup = "./semaphore-mtb-setup"
    if not os.path.exists(semaphore_mtb_setup):
        print("semaphore-mtb-setup not found. Setting up...")
        setup_semaphore_mtb()

    print(f"Verifying {out_file} against {initial_contribution}")
    try:
        result = subprocess.run([semaphore_mtb_setup, "p2v", out_file, initial_contribution], capture_output=True, text=True, timeout=300)
        success = result.returncode == 0
        status = "SUCCESS" if success else "FAILURE"
        print(f"Verification {status}")
        return success, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        print(f"TIMEOUT: Verification timed out after 5 minutes for {out_file}")
        return False, "", "Verification timed out after 5 minutes"

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

def list_bucket_objects(bucket_name, region_name):
    s3 = boto3.client('s3', region_name=region_name)
    try:
        response = s3.list_objects_v2(Bucket=bucket_name)
        return [obj['Key'] for obj in response.get('Contents', [])]
    except ClientError as e:
        print(f"Error listing bucket objects: {e}")
        return []

def download_file(bucket_name, region_name, s3_file, local_file):
    s3 = boto3.client('s3', region_name=region_name)
    try:
        os.makedirs(os.path.dirname(local_file), exist_ok=True)
        s3.download_file(bucket_name, s3_file, local_file)
        return True
    except ClientError as e:
        print(f"Error downloading file {s3_file}: {e}")
        return False

def download_file_worker(bucket_name, region_name, file, contributions_dir):
    parts = file.split('_')
    if parts[-1].endswith(".ph2"):
        number = int(parts[-1].split('.')[0])
        username = parts[-3]
        name = '_'.join(parts[:-2])
        subfolder = os.path.join(contributions_dir, f"{number:04d}_{username}")
    else:
        subfolder = os.path.join(contributions_dir, "0000_initial")
    
    local_path = os.path.join(subfolder, file)
    return f"{'Downloaded' if download_file(bucket_name, region_name, file, local_path) else 'Failed to download'} {file} to {local_path}"

def download_txt_file_worker(bucket_name, region_name, file, subfolder):
    local_path = os.path.join(subfolder, file.split('/')[-1])
    return f"{'Downloaded' if download_file(bucket_name, region_name, file, local_path) else 'Failed to download'} {file} to {local_path}"

def verify_contribution(contributions_dir, verify_logs_dir, subdir):
    parts = subdir.split('_')
    if len(parts) < 2 or not parts[0].isdigit():
        return
    
    number = int(parts[0])
    name = '_'.join(parts[1:])
    
    log_file = os.path.join(verify_logs_dir, f"{number:04d}_{name}.txt")
    
    with open(log_file, 'w') as f:
        f.write(f"Verification for contribution {number:04d} {name}\n\n")
    
    contribution_files = os.listdir(os.path.join(contributions_dir, subdir))
    
    for file in contribution_files:
        if file.endswith('.ph2'):
            file_path = os.path.join(contributions_dir, subdir, file)
            ph2_file = next((ph2 for ph2 in PH2_FILES if file.startswith(ph2)), None)
            
            if ph2_file:
                initial_contribution = os.path.join(contributions_dir, "0000_initial", f"{ph2_file}_initial_contribution_0.ph2")
                
                print(f"Verifying {file_path} against {initial_contribution}")
                success, stdout, stderr = verify_ph2_files(file_path, initial_contribution)
                result_msg = f"Verification of {file_path} against {initial_contribution}: {'Success' if success else 'Failed'}"
                
                with open(log_file, 'a') as f:
                    f.write(f"{result_msg}\n{'Output:' if success else 'Error:'}\n{stdout if success else stderr}\n\n")
                
                if not success:
                    return f"Verification failed for {file_path} against {initial_contribution}"
    
    return f"Verified {number:04d} {name}. For more details, check {log_file}"

def get_local_path(file):
    parts = file.split('_')
    if parts[-1].endswith(".ph2"):
        number = int(parts[-1].split('.')[0])
        username = parts[-3]
        return os.path.join(f"{number:04d}_{username}", file)
    else:
        return os.path.join("0000_initial", file)

def main(bucket_name, region_name, local=False):
    contributions_dir = "./contributions/"
    verify_logs_dir = "./verify_logs/"
    hashes_dir = os.path.join(contributions_dir, "hashes")
    
    os.makedirs(verify_logs_dir, exist_ok=True)
    os.makedirs(contributions_dir, exist_ok=True)
    os.makedirs(hashes_dir, exist_ok=True)
    os.makedirs(os.path.join(contributions_dir, "0000_initial"), exist_ok=True)

    if not local:
        all_files = list_bucket_objects(bucket_name, region_name)
        ph2_files = sorted([obj for obj in all_files if obj.endswith('.ph2')])
        txt_files = sorted([obj for obj in all_files if obj.endswith('.txt')])
        
        new_ph2_files = [file for file in ph2_files if not os.path.exists(os.path.join(contributions_dir, get_local_path(file)))]
        new_txt_files = [file for file in txt_files if not os.path.exists(os.path.join(hashes_dir, file.split('/')[-1]))]
        
        print("AWS All PH2 files:", len(ph2_files))
        print("AWS New PH2 files:", len(new_ph2_files))
        print("AWS All TXT files:", len(txt_files))
        print("AWS New TXT files:", len(new_txt_files))

        with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            ph2_tasks = [executor.submit(download_file_worker, bucket_name, region_name, file, contributions_dir) for file in new_ph2_files]
            txt_tasks = [executor.submit(download_txt_file_worker, bucket_name, region_name, file, hashes_dir) for file in new_txt_files]
            
            for future in as_completed(ph2_tasks + txt_tasks):
                try:
                    result = future.result()
                    print(result)
                except Exception as e:
                    print(f"Error in download task: {str(e)}")
                    traceback.print_exc()

    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        verify_tasks = [executor.submit(verify_contribution, contributions_dir, verify_logs_dir, subdir) 
                        for subdir in sorted(os.listdir(contributions_dir)) 
                        if os.path.isdir(os.path.join(contributions_dir, subdir)) and subdir != "0000_initial"]
        
        for future in as_completed(verify_tasks):
            try:
                result = future.result()
                if result:
                    print(result)
            except Exception as e:
                print(f"Error in verification task: {str(e)}")
                traceback.print_exc()

    if any(future.exception() is not None for future in verify_tasks):
        print("Some verification tasks failed. Check the logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    local_flag = '--local' in sys.argv

    if local_flag:
        if len(sys.argv) != 2:
            print("Usage: python3 ./coordinator/verify_contributions.py --local")
            sys.exit(1)
        main(None, None, local_flag)
    else:
        if len(sys.argv) != 3:
            print("Usage: python3 ./coordinator/verify_contributions.py <bucket_name> <region_name>")
            sys.exit(1)
        bucket_name = sys.argv[1]
        region_name = sys.argv[2]
        main(bucket_name, region_name, local_flag)
