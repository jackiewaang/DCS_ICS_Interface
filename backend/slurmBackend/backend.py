import json
import logging
import shlex
import subprocess
import time
from dataclasses import dataclass
from uuid import uuid4

from .config import SlurmConfig
from .models import ada_models, gecko_models, gemma_partitions

logger = logging.getLogger(__name__)

@dataclass
class EmbeddingJobRequest:
    texts: list[str]
    model_name: str
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
            "texts": request.texts,
            "model_name": request.model_name,
            "prompt": request.prompt
        }

        return self._run_job(
            script=self.config.embedding_script,
            payload=payload
        )

    # Wrapper on submit_job to run LLM jobs
    def run_llm(self, payload: dict, model_name: str):
        partitions = []
        if model_name in ada_models:
            partitions.append("wmlg-ada")
        if model_name in gecko_models:
            partitions.append("gecko")
        if not partitions:
            raise ValueError(f"Unsupported Slurm LLM model: {model_name}")

        return self._run_partitioned_job(
            script=self.config.llm_script,
            payload={**payload, "model_name": model_name},
            model_name=model_name,
            partitions=partitions,
        )

    def run_gemma(self, payload: dict):
        return self._run_partitioned_job(
            script=self.config.gemma_script,
            payload=payload,
            model_name="Gemma 3 12B fine-tuned",
            partitions=gemma_partitions,
        )

    def _run_partitioned_job(
        self, script: str, payload: dict, model_name: str, partitions: list[str],
    ):
        if not partitions:
            raise ValueError(f"No Slurm partitions configured for model: {model_name}")

        for index, partition in enumerate(partitions):
            logger.info("Slurm LLM attempt model=%s partition=%s", model_name, partition)
            try:
                # Each attempt gets its own request directory and timeout.
                return self._run_job(
                    script=script,
                    payload=payload,
                    partition=partition,
                )
            except SlurmAllocationTimeout as exc:
                if index == len(partitions) - 1:
                    raise SlurmAllocationTimeout(
                        f"Model {model_name} was not allocated on any eligible "
                        f"partition: {', '.join(partitions)}."
                    ) from exc
                logger.warning(
                    "Slurm LLM allocation timed out model=%s partition=%s fallback=%s",
                    model_name, partition, partitions[index + 1],
                )

    # Main function running full lifecycle of a job
    def _run_job(self, script: str, payload: dict, partition: str | None = None):

        request_id = str(uuid4())
        remote_dir = f"{self.config.remote_job_dir.rstrip('/')}/{request_id}"
        started_at = time.monotonic()
        logger.info(
            "Slurm request started request_id=%s script=%s payload_keys=%s",
            request_id,
            script,
            sorted(payload.keys()),
        )

        try:
            self._write_input(remote_dir, payload)
            logger.info("Slurm input written request_id=%s", request_id)

            job_id = self._submit_job(
                script=script,
                remote_dir=remote_dir,
                partition=partition,
            )
            logger.info(
                "Slurm job submitted request_id=%s job_id=%s partition=%s elapsed_seconds=%.2f",
                request_id,
                job_id,
                partition,
                time.monotonic() - started_at,
            )

            allocated = self._wait_for_allocation(job_id)

            if not allocated:
                logger.warning(
                    "Slurm allocation failed request_id=%s job_id=%s elapsed_seconds=%.2f",
                    request_id,
                    job_id,
                    time.monotonic() - started_at,
                )
                self._cancel_job(job_id)
                raise SlurmAllocationTimeout(
                    f"Job {job_id} was not allocated within the "
                    f"{self.config.allocation_timeout}s timeout."
                )

            try:
                final_state = self._wait_for_completion(job_id)
            except SlurmCompletionTimeout:
                logger.warning(
                    "Slurm completion timed out request_id=%s job_id=%s elapsed_seconds=%.2f",
                    request_id,
                    job_id,
                    time.monotonic() - started_at,
                )
                self._cancel_job(job_id)
                raise

            logger.info(
                "Slurm job reached terminal state request_id=%s job_id=%s state=%s elapsed_seconds=%.2f",
                request_id,
                job_id,
                final_state,
                time.monotonic() - started_at,
            )
            if final_state != "COMPLETED":
                raise RuntimeError(
                    f"Slurm job {job_id} failed with state: {final_state}"
                )
            
            result = self._read_result(remote_dir)
            logger.info(
                "Slurm result read request_id=%s job_id=%s elapsed_seconds=%.2f result_type=%s",
                request_id,
                job_id,
                time.monotonic() - started_at,
                type(result).__name__,
            )
            return result
        
        finally:
            self._cleanup(remote_dir)
          
    def _submit_job(self, script: str, remote_dir: str, partition: str | None = None) -> str:
        """
        Submits job to Slurm and returns job ID
        """

        partition_option = f"--partition={shlex.quote(partition)} " if partition else ""
        command = (
            f"sbatch --parsable "
            f"{partition_option}"
            f"--output={shlex.quote(f'{remote_dir}/joboutput_%j.out')} "
            f"--error={shlex.quote(f'{remote_dir}/joboutput_%j.err')} "
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
        Returns False only on allocation timeout; terminal failures raise.
        """
        
        deadline = time.monotonic() + self.config.allocation_timeout

        previous_state = None
        while time.monotonic() < deadline:
            state = self._get_job_state(job_id)
            if state != previous_state:
                logger.info("Slurm allocation state job_id=%s state=%s", job_id, state)
                previous_state = state

            if state in {"RUNNING", "COMPLETING", "COMPLETED"}:
                return True

            if state in {
                "FAILED",
                "CANCELLED",
                "TIMEOUT",
                "NODE_FAIL",
                "OUT_OF_MEMORY"
            }:
                raise RuntimeError(f"Slurm job {job_id} failed with state: {state}")

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

        previous_state = None
        while time.monotonic() < deadline:
            state = self._get_job_state(job_id)
            if state != previous_state:
                logger.info("Slurm completion state job_id=%s state=%s", job_id, state)
                previous_state = state

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
