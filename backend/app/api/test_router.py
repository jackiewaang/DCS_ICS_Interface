# test_router.py

from backend_router import (
    AquiferBackend,
    AquiferConfig,
    InferenceRouter,
    SlurmBackend,
    SlurmConfig,
)


slurm = SlurmBackend(
    SlurmConfig(
        ssh_host="u2261259@kudu-taught",
        job_script="~/test_job.sh",
        queue_timeout=10,
        poll_interval=2,
    )
)

aquifer = AquiferBackend(
    AquiferConfig(
        embedding_url="http://localhost:18001"
    )
)

router = InferenceRouter(
    slurm=slurm,
    aquifer=aquifer,
)

result = router.embed(
    ["This is a test sentence."]
)

print(result)
