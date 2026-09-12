"""Partition lifecycle tests; no SSH or Slurm cluster required."""

import shlex
import subprocess
import unittest
from unittest.mock import Mock, patch

from . import models
from .backend import (
    EmbeddingJobRequest,
    SlurmAllocationTimeout,
    SlurmBackend,
    SlurmCompletionTimeout,
)
from .config import SlurmConfig


class PartitionRoutingTests(unittest.TestCase):
    def setUp(self):
        self.backend = SlurmBackend(SlurmConfig(
            ssh_host="host", proxy_jump="jump", remote_job_dir="jobs",
            remote_repo_dir="repo", embedding_script="embedding.sbatch",
            llm_script="llm.sbatch", gemma_script="gemma.sbatch",
            poll_interval=2, allocation_timeout=120, completion_timeout=900,
        ))
        self.model = models.SLURM_LLM_MODELS[0]
        self.backend._write_input = Mock()
        self.backend._submit_job = Mock(side_effect=["1", "2"])
        self.backend._wait_for_allocation = Mock(return_value=True)
        self.backend._wait_for_completion = Mock(return_value="COMPLETED")
        self.backend._cancel_job = Mock()
        self.backend._read_result = Mock(return_value={"answer": "ok"})
        self.backend._cleanup = Mock()

    def partitions(self):
        return [call.kwargs["partition"] for call in self.backend._submit_job.call_args_list]

    def test_model_list_preserves_order_and_deduplicates(self):
        self.assertEqual(models.SLURM_LLM_MODELS, list(dict.fromkeys(
            models.gecko_models + models.ada_models,
        )))
        self.assertEqual(models.SLURM_LLM_MODELS, [
            "Qwen/Qwen3-4B-Instruct-2507", "Qwen/Qwen3-8B",
        ])

    def test_ada_success(self):
        self.assertEqual(self.backend.run_llm({}, self.model), {"answer": "ok"})
        self.assertEqual(self.partitions(), ["wmlg-ada"])
        self.backend._cancel_job.assert_not_called()

    def test_timeout_cancels_before_fallback_and_isolates_results(self):
        self.backend._wait_for_allocation.side_effect = [False, True]
        events = Mock()
        events.attach_mock(self.backend._submit_job, "submit")
        events.attach_mock(self.backend._cancel_job, "cancel")
        self.backend.run_llm({}, self.model)
        self.assertEqual(self.partitions(), ["wmlg-ada", "gecko"])
        self.assertEqual([call[0] for call in events.mock_calls], ["submit", "cancel", "submit"])
        self.backend._cancel_job.assert_called_once_with("1")
        directories = [call.args[0] for call in self.backend._write_input.call_args_list]
        self.assertNotEqual(*directories)
        self.backend._read_result.assert_called_once_with(directories[1])
        self.assertEqual([call.args[0] for call in self.backend._cleanup.call_args_list], directories)

    def test_single_partition_models(self):
        for ada, gecko, expected in [([self.model], [], "wmlg-ada"), ([], [self.model], "gecko")]:
            with self.subTest(partition=expected), patch(
                "backend.slurmBackend.backend.ada_models", ada,
            ), patch("backend.slurmBackend.backend.gecko_models", gecko):
                self.backend._submit_job.reset_mock()
                self.backend.run_llm({}, self.model)
                self.assertEqual(self.partitions(), [expected])

    def test_unknown_model_rejected_before_remote_work(self):
        with self.assertRaises(ValueError):
            self.backend.run_llm({}, "unknown")
        self.backend._write_input.assert_not_called()
        self.backend._submit_job.assert_not_called()

    def test_all_partitions_exhausted(self):
        self.backend._wait_for_allocation.return_value = False
        with self.assertRaisesRegex(SlurmAllocationTimeout, "wmlg-ada, gecko"):
            self.backend.run_llm({}, self.model)
        self.assertEqual(self.partitions(), ["wmlg-ada", "gecko"])
        self.assertEqual(self.backend._cancel_job.call_count, 2)
        self.backend._read_result.assert_not_called()

    def test_ada_only_timeout_has_no_fallback(self):
        self.backend._wait_for_allocation.return_value = False
        with patch("backend.slurmBackend.backend.gecko_models", []):
            with self.assertRaises(SlurmAllocationTimeout):
                self.backend.run_llm({}, self.model)
        self.assertEqual(self.partitions(), ["wmlg-ada"])

    def test_cancellation_failure_stops_fallback(self):
        self.backend._wait_for_allocation.return_value = False
        self.backend._cancel_job.side_effect = subprocess.CalledProcessError(1, "scancel")
        with self.assertRaises(subprocess.CalledProcessError):
            self.backend.run_llm({}, self.model)
        self.assertEqual(self.partitions(), ["wmlg-ada"])

    def test_submission_failure_does_not_retry(self):
        self.backend._submit_job.side_effect = subprocess.CalledProcessError(1, "sbatch")
        with self.assertRaises(subprocess.CalledProcessError):
            self.backend.run_llm({}, self.model)
        self.assertEqual(self.partitions(), ["wmlg-ada"])

    def test_execution_failure_does_not_retry(self):
        self.backend._wait_for_completion.return_value = "OUT_OF_MEMORY"
        with self.assertRaisesRegex(RuntimeError, "OUT_OF_MEMORY"):
            self.backend.run_llm({}, self.model)
        self.assertEqual(self.partitions(), ["wmlg-ada"])

    def test_completion_timeout_cancels_without_retry(self):
        self.backend._wait_for_completion.side_effect = SlurmCompletionTimeout("expired")
        with self.assertRaises(SlurmCompletionTimeout):
            self.backend.run_llm({}, self.model)
        self.assertEqual(self.partitions(), ["wmlg-ada"])
        self.backend._cancel_job.assert_called_once_with("1")

    def test_early_terminal_failure_does_not_retry(self):
        self.backend._wait_for_allocation = SlurmBackend._wait_for_allocation.__get__(self.backend)
        self.backend._get_job_state = Mock(return_value="FAILED")
        with self.assertRaisesRegex(RuntimeError, "FAILED"):
            self.backend.run_llm({}, self.model)
        self.assertEqual(self.partitions(), ["wmlg-ada"])

    def test_each_allocation_wait_has_full_timeout(self):
        self.backend._get_job_state = Mock(return_value="PENDING")
        with patch("backend.slurmBackend.backend.time.monotonic", side_effect=[
            0, 0, 119, 120, 200, 200, 319, 320,
        ]), patch("backend.slurmBackend.backend.time.sleep"):
            for job in ["1", "2"]:
                self.assertFalse(SlurmBackend._wait_for_allocation(self.backend, job))
        self.assertEqual(self.backend._get_job_state.call_count, 4)

    def test_submission_partition_override_and_default(self):
        self.backend._ssh = Mock(return_value="123;cluster")
        for partition in ["wmlg-ada", "gecko", None]:
            self.assertEqual(SlurmBackend._submit_job(
                self.backend, "llm script.sbatch", "jobs/attempt", partition,
            ), "123")
            arguments = shlex.split(self.backend._ssh.call_args.args[0])
            partition_args = [arg for arg in arguments if arg.startswith("--partition=")]
            self.assertEqual(partition_args, [f"--partition={partition}"] if partition else [])
            self.assertEqual(arguments[-3:], ["llm script.sbatch", "jobs/attempt", "repo"])

    def test_embedding_keeps_script_default(self):
        self.backend.run_embedding(EmbeddingJobRequest(["text"], "embedding-model"))
        self.assertEqual(self.partitions(), [None])
        self.assertEqual(self.backend._submit_job.call_args.kwargs["script"], "embedding.sbatch")

    def test_gemma_ada_success_keeps_dedicated_script_and_payload(self):
        payload = {"summary": "text", "research": "research", "impact": "impact"}
        self.assertEqual(self.backend.run_gemma(payload), {"answer": "ok"})
        self.assertEqual(self.partitions(), ["wmlg-ada"])
        self.assertEqual(self.backend._submit_job.call_args.kwargs["script"], "gemma.sbatch")
        self.assertEqual(self.backend._write_input.call_args.args[1], payload)

    def test_gemma_timeout_falls_back_with_separate_directories(self):
        self.backend._wait_for_allocation.side_effect = [False, True]
        events = Mock()
        events.attach_mock(self.backend._submit_job, "submit")
        events.attach_mock(self.backend._cancel_job, "cancel")
        self.backend.run_gemma({"summary": "text"})
        self.assertEqual(self.partitions(), ["wmlg-ada", "gecko"])
        self.assertEqual([call[0] for call in events.mock_calls], ["submit", "cancel", "submit"])
        directories = [call.args[0] for call in self.backend._write_input.call_args_list]
        self.assertNotEqual(*directories)
        self.backend._read_result.assert_called_once_with(directories[1])
        self.assertTrue(all(call.kwargs["script"] == "gemma.sbatch"
                            for call in self.backend._submit_job.call_args_list))

    def test_gemma_exhausted_partitions(self):
        self.backend._wait_for_allocation.return_value = False
        with self.assertRaisesRegex(SlurmAllocationTimeout, "wmlg-ada, gecko"):
            self.backend.run_gemma({})
        self.assertEqual(self.backend._cancel_job.call_count, 2)

    def test_gemma_ada_only_timeout(self):
        self.backend._wait_for_allocation.return_value = False
        with patch("backend.slurmBackend.backend.gemma_partitions", ["wmlg-ada"]):
            with self.assertRaises(SlurmAllocationTimeout):
                self.backend.run_gemma({})
        self.assertEqual(self.partitions(), ["wmlg-ada"])

    def test_gemma_errors_do_not_fall_back(self):
        for method, error in [
            ("_submit_job", RuntimeError("submission failed")),
            ("_wait_for_allocation", RuntimeError("FAILED")),
            ("_wait_for_completion", RuntimeError("OUT_OF_MEMORY")),
            ("_wait_for_completion", SlurmCompletionTimeout("expired")),
            ("_cancel_job", RuntimeError("cancellation failed")),
        ]:
            with self.subTest(method=method, error=str(error)):
                self.setUp()
                getattr(self.backend, method).side_effect = error
                if method == "_cancel_job":
                    self.backend._wait_for_allocation.return_value = False
                with self.assertRaises(type(error)):
                    self.backend.run_gemma({})
                self.assertEqual(self.partitions(), ["wmlg-ada"])

    def test_gemma_is_rejected_by_main_llm_pipeline(self):
        for name in ["Gemma 3 12B fine-tuned", "google/gemma-3-12b-it"]:
            self.assertNotIn(name, models.SLURM_LLM_MODELS)
            with self.assertRaises(ValueError):
                self.backend.run_llm({}, name)
        self.backend._submit_job.assert_not_called()

    def test_gemma_empty_partitions_rejected(self):
        with patch("backend.slurmBackend.backend.gemma_partitions", []):
            with self.assertRaisesRegex(ValueError, "No Slurm partitions"):
                self.backend.run_gemma({})
        self.backend._write_input.assert_not_called()


if __name__ == "__main__":
    unittest.main()
