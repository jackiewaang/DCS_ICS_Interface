import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

SLURM_ENV_PATH = Path(__file__).resolve().with_name(".env")

@dataclass
class SlurmConfig:
    ssh_host: str
    proxy_jump: str
    remote_job_dir: str
    remote_repo_dir: str
    embedding_script: str
    llm_script: str
    poll_interval: float
    allocation_timeout: float
    completion_timeout: float

    @classmethod
    def from_env(cls):
        load_dotenv(SLURM_ENV_PATH, override=False)
        return cls(
            ssh_host=os.getenv("SLURM_SSH_HOST", "default_host"),
            proxy_jump=os.getenv("SLURM_PROXY_JUMP", "default_jump"),
            remote_job_dir=os.getenv("SLURM_REMOTE_JOB_DIR", "jobs"),
            remote_repo_dir=os.getenv("SLURM_REMOTE_REPO_DIR", "DCS_ICS_Interface"),
            embedding_script=os.getenv(
                "SLURM_EMBEDDING_SCRIPT",
                "DCS_ICS_Interface/backend/slurmBackend/run_embedding.sbatch",
            ),
            llm_script=os.getenv(
                "SLURM_LLM_SCRIPT",
                "DCS_ICS_Interface/backend/slurmBackend/run_llm.sbatch",
            ),
            poll_interval=float(os.getenv("SLURM_POLL_INTERVAL", "2")),
            allocation_timeout=float(os.getenv("SLURM_ALLOCATION_TIMEOUT", "30")),
            completion_timeout=float(os.getenv("SLURM_COMPLETION_TIMEOUT", "600")),
        )
