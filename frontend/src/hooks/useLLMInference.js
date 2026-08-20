import { useEffect, useState } from 'react';
import { api } from '@/services/api';

const POLLING_INTERVAL_MS = 2500;

const EMPTY_LLM_STATE = {
  inferenceId: null,
  result: null,
  status: 'idle',
  errorMessage: '',
};

export default function useLLMInference(inferenceId) {
  const [llmState, setLlmState] = useState(EMPTY_LLM_STATE);

  useEffect(() => {
    if (!inferenceId) {
      return undefined;
    }

    let isCancelled = false;
    let intervalId;

    const pollLLMInference = async () => {
      try {
        const result = await api.getLLMInference(inferenceId);
        if (isCancelled) {
          return;
        }

        setLlmState({
          inferenceId,
          result,
          status: result.status || 'running',
          errorMessage: result.status === 'error' ? result.error_message || '' : '',
        });

        if (['completed', 'error', 'not_found'].includes(result.status)) {
          window.clearInterval(intervalId);
        }
      } catch (error) {
        if (isCancelled) {
          return;
        }

        setLlmState({
          inferenceId,
          result: null,
          status: 'error',
          errorMessage: error.message,
        });
        window.clearInterval(intervalId);
      }
    };

    intervalId = window.setInterval(pollLLMInference, POLLING_INTERVAL_MS);
    pollLLMInference();

    return () => {
      isCancelled = true;
      window.clearInterval(intervalId);
    };
  }, [inferenceId]);

  return llmState;
}
