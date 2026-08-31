import json
import shlex
import subprocess
import time
from dataclasses import dataclass
from uuid import uuid4

from .config import SlurmConfig

@dataclass
class EmbeddingJobRequest:
    summary: str
    research: str
    details: str
    prompt: str | None = None

class SlurmAllocationTimeout(Exception):
    pass


class SlurmCompletionTimeout(Exception):
    pass


class SlurmBackend:
    def __init__(self, config: SlurmConfig):
        self.config = config

    # Wrapper on submit_job to run embedding jobs
    def run_embedding(self, request: EmbeddingJobRequest):
        payload = {
            "summary": request.summary,
            "research": request.research,
            "details": request.details,
            "prompt": request.prompt
        }

        return self._run_job(
            script=self.config.embedding_script,
            payload=payload
        )

    # Wrapper on submit_job to run LLM jobs
    def run_llm(self, payload: dict):
        return self._run_job(
            script=self.config.llm_script,
            payload=payload,
        )

    # Main function running full lifecycle of a job
    def _run_job(self, script: str, payload: dict):

        request_id = str(uuid4())
        remote_dir = f"{self.config.remote_job_dir.rstrip('/')}/{request_id}"

        try:
            self._write_input(remote_dir, payload)

            job_id = self._submit_job(
                script=script,
                remote_dir=remote_dir
            )

            allocated = self._wait_for_allocation(job_id)

            if not allocated:
                self._cancel_job(job_id)
                raise SlurmAllocationTimeout(
                    f"Job {job_id} was not allocated within the "
                    f"{self.config.allocation_timeout}s timeout."
                )

            try:
                final_state = self._wait_for_completion(job_id)
            except SlurmCompletionTimeout:
                self._cancel_job(job_id)
                raise

            if final_state != "COMPLETED":
                raise RuntimeError(
                    f"Slurm job {job_id} failed with state: {final_state}"
                )
            
            return self._read_result(remote_dir)
        
        finally:
            self._cleanup(remote_dir)

    def _submit_job(self, script: str, remote_dir: str) -> str:
        """
        Submits job to Slurm and returns job ID
        """

        command = (
            f"sbatch --parsable "
            f"{shlex.quote(script)} "
            f"{shlex.quote(remote_dir)} "
            f"{shlex.quote(self.config.remote_repo_dir)}"
        )

        output = self._ssh(command)

        return output.strip().split(";")[0]

    def _write_input(self, remote_dir: str, payload: dict):
        """
        Writes input payload to remote directory as input.json
        """

        payload_json = json.dumps(payload)

        # quote path and JSON
        quoted_dir = shlex.quote(remote_dir)
        quoted_payload = shlex.quote(payload_json)

        command = (
            f"mkdir -p {quoted_dir} &&"
            f"printf '%s' {quoted_payload} > {quoted_dir}/input.json"
        )

        self._ssh(command)

    def _wait_for_allocation(self, job_id: str) -> bool:
        """
        Polls job state until allocated or timeout fails
        """
        
        deadline = time.monotonic() + self.config.allocation_timeout

        while time.monotonic() < deadline:
            state = self._get_job_state(job_id)

            if state in {"RUNNING", "COMPLETING", "COMPLETED"}:
                return True

            if state in {
                "FAILED",
                "CANCELLED",
                "TIMEOUT",
                "NODE_FAIL",
                "OUT_OF_MEMORY"
            }:
                return False

            time.sleep(self.config.poll_interval)
        
        return False

    def _cancel_job(self, job_id: str):

        """
        Cancels a job in Slurm system
        """

        self._ssh(
            f"scancel {shlex.quote(job_id)}"
        )

    def _wait_for_completion(self, job_id: str) -> str:
        """
        Polls state of running job until completed or failed
        """

        deadline = time.monotonic() + self.config.completion_timeout

        while time.monotonic() < deadline:
            state = self._get_job_state(job_id)

            if state in {
                "COMPLETED",
                "FAILED",
                "CANCELLED",
                "TIMEOUT",
                "NODE_FAIL",
                "OUT_OF_MEMORY"
            }:
                return state
            
            time.sleep(self.config.poll_interval)

        raise SlurmCompletionTimeout(
            f"Job {job_id} did not complete within the "
            f"{self.config.completion_timeout}s timeout."
        )

    def _get_job_state(self, job_id: str) -> str:
        """Returns the current Slurm state for a submitted job."""
        state = self._ssh(
            f"squeue -h -j {shlex.quote(job_id)} -o '%T'"
        )

        if state:
            return state.splitlines()[0].strip().upper()

        # Completed jobs can disappear from squeue before the next poll.
        state = self._ssh(
            f"sacct -n -X -j {shlex.quote(job_id)} --format=State --parsable2"
        )
        if not state:
            return "UNKNOWN"

        return state.splitlines()[0].strip().split("|")[0].upper()

    def _read_result(self, remote_dir: str) -> dict:
        """
        Reads output.json from remote dir and returns as dict
        """

        output = self._ssh(
            f"cat {shlex.quote(remote_dir)}/output.json"
        )

        return json.loads(output)
    
    def _cleanup(self, remote_dir: str):

        """
        Cleans up remote directory after job completion
        """

        self._ssh(
            f"rm -rf {shlex.quote(remote_dir)}"
        )

    def _ssh(self, command: str) -> str:
        result = subprocess.run(
            [
                "ssh",
                "-J",
                self.config.proxy_jump,
                self.config.ssh_host,
                command
            ],
            capture_output=True,
            text=True,
            check=True
        )

        return result.stdout.strip()
