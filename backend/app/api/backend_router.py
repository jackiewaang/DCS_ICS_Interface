import subprocess
import time
from dataclasses import dataclass

import requests


@dataclass
class SlurmConfig:
    ssh_host: str
    job_script: str
    queue_timeout: int = 120
    poll_interval: int = 2

@dataclass
class AquiferConfig:
    embedding_url: str

class SlurmBackend:
    def __init__(self, config: SlurmConfig):
        self.config = config

    def _ssh(self, command: str) -> str:
        result = subprocess.run(
            [
                "ssh",
                "-J", 
                "dcs",
                self.config.ssh_host,
                command
            ],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    
    def submit(self) -> str:
        output = self._ssh(
            f"sbatch --parsable {self.config.job_script}"
        )
        job_id = output.strip().split()[-1]

        return job_id
    
    def get_state(self, job_id: str) -> str:
        return self._ssh(
            f"squeue -h -j {job_id} -o '%T'"
        )
    
    def cancel(self, job_id: str) -> None:
        self._ssh(f"scancel {job_id}")

    def wait_for_allocation(self, job_id: str) -> None:
        deadline = time.monotonic() + self.config.queue_timeout

        while time.monotonic() < deadline:
            state = self.get_state(job_id)

            print(f"Job {job_id}: {state}")

            if state in {"RUNNING", "COMPLETING", "COMPLETED"}:
                return True

            if state not in {
                "PENDING",
                "CONFIGURING"
            }:
                print(f"Unexpected Slurm State: {state}")
                return False
            
            time.sleep(self.config.poll_interval)
        
        return False


class AquiferBackend:
    def __init__(self, config: AquiferConfig):
        self.config = config

    def embed(
        self,
        texts: list[str],
        prompt: str | None = None
    ):
        response = requests.post(
            f"{self.config.embedding_url}/embed",
            json={
                "texts": texts,
                "prompt": prompt
            },
            timeout=120
        )

        response.raise_for_status()
        return response.json()

class InferenceRouter:
    def __init__(
        self,
        slurm: SlurmBackend,
        aquifer: AquiferBackend
    ):
        self.slurm = slurm
        self.aquifer = aquifer
    
    def embed(
        self,
        texts: list[str],
        prompt: str | None = None
    ):
        try:
            print("Trying Slurm backend...")

            job_id = self.slurm.submit()
            print(f"Submitted job {job_id} to Slurm backend.")

            allocated = self.slurm.wait_for_allocation(job_id)

            if allocated:
                return {
                    "backend": "slurm",
                    "job_id": job_id,
                    "status": "allocated",
                }

            print("Queue timeout reached. Cancelling job and falling back to Aquifer backend.")
            self.slurm.cancel(job_id)

        except subprocess.CalledProcessError as e:
            print(f"Slurm backend failed with error: {e}. Falling back to Aquifer backend.")
        
        result = self.aquifer.embed(
            texts=texts,
            prompt=prompt
        )

        return {
            "backend": "aquifer",
            "result": result
        }
