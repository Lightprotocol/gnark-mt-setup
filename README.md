# Light Protocol Trusted Setup
Light introduces ZK Compression, a primitive in Solana scaling and interop. Light compresses account state by committing data as leaves to Merkle trees, allowing apps and smart contracts to interact with data stored outside the onchain account space. To keep the witness size small, Light uses [Gnark groth16 proofs based on Worldcoin's Semaphore adaptation](https://github.com/Lightprotocol/light-protocol/tree/main/light-prover/prover).

Groth16 proofs require a two-phase trusted setup:

* (1) Universal "Powers of Tau" ceremony (phase 1)
* (2) Circuit-specific setup (phase 2)

For (1) we are using the [Perpetual Powers of Tau ceremony](https://github.com/privacy-scaling-explorations/perpetualpowersoftau) (up to contribution #54) via the s3 hosted bucket in the [snarkjs repo](https://github.com/iden3/snarkjs/blob/master/README.md#7-prepare-phase-2) README. We used a deserializer built by the Worldcoin team to convert it from the .ptau format into the .ph1 format used by gnark and initialized a phase 2 using Worldcoin's [fork](https://github.com/worldcoin/semaphore-mtb-setup) of a ceremony coordinator wrapper on top of gnark built by the [zkbnb](https://github.com/bnb-chain/zkbnb-setup/) team.

## How to Participate in the Trusted Setup

### Requirements

-  your machine must have Bash and curl installed. (Verify by running ```bash --version``` and ```curl --version```)

### Steps

1. (Recommended) Verify the current contribution you're building on using the verification script. (See "How to Verify")
2. Run the contribute curl command sent to you by the coordinator:
   - Executes the `./contribute.sh` gist (looks like [this](https://gist.githubusercontent.com/SwenSchaeferjohann/c50c4149ea86f43592083c1da25e8ef8/raw/83a5e76867d46897779c60ba8775eb0c3b1c483f/abctest.sh)) script with your name/pseudonym, the contribution number, and the presigned URLs received from the coordinator.
   - The scripts downloads dependencies, the last contribution, adds your own, and uploads the result to the coordinator's s3 bucket.
3. Please store your contribution hash and attest to it (e.g., social media, PGP signed email).
4. Take steps to defend against attacks as you deem necessary, e.g. by wiping your RAM/SSD after you're done.

## How to Verify

### Requirements to verify

- Python 3.10+
- Install Git: [Git Installation Guide](https://github.com/git-guides/install-git)
- Install Go: [Go Installation Guide](https://go.dev/doc/install)
- Minimum 16GB RAM 
- Download [Semaphore-mtb-setup](https://github.com/worldcoin/semaphore-mtb-setup):
   ```
   git clone https://github.com/worldcoin/semaphore-mtb-setup
   ```
   ```
   cd semaphore-mtb-setup && go build -v && cd ../
   ```

Now run the verification of all previous contributions:

0. Download this repo
   ```
   git clone https://github.com/Lightprotocol/gnark-mt-setup.git
   ```

1. Activate the virtual environment:
   ```
   source venv/bin/activate
   ```
2. Run the verification script:
   ```
   python3 coordinator/verify_contributions.py --local
   ```
3. Check the contribution hashes in ```./contributions/hashes``` against those attested to by the contributors.

## Coordinator Section

The coordinator is responsible for managing the setup process.

Executed once:

1. In light-protocol monorepo, checkout: [swen/t-setup](https://github.com/Lightprotocol/light-protocol/blob/swen/t-setup/scripts/tsc-create-r1cs.sh), then run:
   ```
   ./scripts/tsc-create-r1cs.sh
   ```
(This will download the ptau for power 16, convert it into a ph1 file, and extract the R1CS and convert it into .ph2 files for all our circuits.)

2. Set up an AWS S3 bucket with object lock and versioning enabled
3. Rename the initial contributions (phase 2 files) in the format: `<circuit_name><your_name>_contribution_0.ph2`
4. Upload them to the AWS S3 bucket.


Now, for every contributor:

- Use the coordinator script to create presigned URLs and manage contributions:
  ```
  brew install awscli && aws configure
  ```
  ```
  ./coordinator/create-urls.sh <bucket_name> <next_contributor_name> <contribution_number> <previous_contributor_name>
  ```
- Copy the command's output (a curl script with presigned URLs) to clipboard and share it with the next contributor via a secure channel.
- Once the contributor has uploaded their ph2 files, verify the new contributions by running:
  ```
  ./coordinator/verify_contributions.py <bucket_name>
  ```
- git push the latest contribution to this repo.
  

## Thank You

Special thanks to:
- dcbuilder and worldcoin (for the semaphore-mtb-setup tools)
- the snarkjs team (for hosting the ptau files)
- the zk community (for the ptau ceremony)
