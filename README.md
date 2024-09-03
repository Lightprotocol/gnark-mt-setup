# Trusted Setup for Light Protocol's Gnark Merkle Tree Circuits

Groth16 proofs require a two-phase trusted setup:
1. Universal "Powers of Tau" ceremony (phase 1)
2. Circuit-specific setup (phase 2)

We aim to generate Light Protocol's GMT verifying keys through a multi-organization trusted setup to enhance soundness.

We're reusing an existing phase 1 setup with 54 contributions. [More info](link) and [downloadable .ptau files](link) are available.

## Coordinator and Verification Tool

### Requirements

- [Semaphore-mtb-setup](https://github.com/worldcoin/semaphore-mtb-setup)
- Python 3.10+
- AWS CLI with configured credentials (coordinator only)
- Git
- Go
- Minimum 16GB RAM

### Installation

1. Install Git: [Git Installation Guide](https://github.com/git-guides/install-git)
2. Install Go: [Go Installation Guide](https://go.dev/doc/install)

## How to Contribute to the Trusted Setup

1. Verify the current contribution you're building on using the verification script. (See "How to Verify")
2. Run the contribute curl command provided by the coordinator:
   - Execute the `./contribute.sh` script with your name/pseudonym, the contribution number, and the presigned URLs received from the coordinator.
   - This script will download the last contribution, add your own, and upload the result to the coordinator.
3. Store your contribution hash and attest to it (e.g., social media, PGP signed email).

## How to Verify

1. Ensure you have all the requirements installed.
2. Activate the virtual environment:
   ```
   source venv/bin/activate
   ```
3. Run the verification script:
   ```
   python3 coordinator/verify_contributions.py --local
   ```
4. Check the contribution hashes against those attested by the contributors.

## Coordinator Section

The coordinator is responsible for managing the setup process:
- Generate the R1CS representations of Light's circuits and convert them into phase 2 files.
- Set up an AWS S3 bucket with object lock and versioning enabled, and configure the AWS CLI.
- Upload initial contributions (phase 2 files) to AWS S3, naming them in the format: `<circuit_name><your_name>_contribution_0.ph2`
- Use the coordinator script to create presigned URLs and manage contributions:
  ```
  ./coordinator/create-urls.sh <bucket_name> <next_contributor_name> <contribution_number> <previous_contributor_name>
  ```
- Share the curl script/presigned URLs with the next contributor via a secure channel.
- Verify the new contribution integrity by running:
  ```
  ./coordinator/verify_contributions.py <bucket_name>
  ```

## Thank You

Special thanks to:
- dcbuilder and worldcoin (for the semaphore-mtb-setup tool)
- the snarkjs team (for hosting the ptau files)
- the zk community (for the ptau ceremony)