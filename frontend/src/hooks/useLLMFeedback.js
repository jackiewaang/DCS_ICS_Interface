import { useEffect, useState } from 'react';
import { api } from '@/services/api';

const LLM_TIMEOUT_MS = 305_000;

const EMPTY_LLM_STATE = {
  input: null,
  result: null,
  status: 'idle',
  errorMessage: '',
};

export default function useLLMFeedback(llmInput) {
  const [llmState, setLlmState] = useState(EMPTY_LLM_STATE);

  useEffect(() => {
    if (!llmInput) {
      return undefined;
    }

    const controller = new AbortController();
    let isCancelled = false;
    let didTimeout = false;
    const timeoutId = window.setTimeout(() => {
      didTimeout = true;
      controller.abort();
    }, LLM_TIMEOUT_MS);

    api.getLLMFeedback(llmInput, controller.signal)
      .then((result) => {
        window.clearTimeout(timeoutId);
        if (!isCancelled) {
          setLlmState({ input: llmInput, result, status: 'completed', errorMessage: '' });
        }
      })
      .catch((error) => {
        window.clearTimeout(timeoutId);
        if (!isCancelled && (didTimeout || error.name !== 'AbortError')) {
          setLlmState({
            input: llmInput,
            result: null,
            status: 'error',
            errorMessage: didTimeout
              ? 'AI insight generation timed out after five minutes.'
              : error.message,
          });
        }
      });

    return () => {
      isCancelled = true;
      window.clearTimeout(timeoutId);
      controller.abort();
    };
  }, [llmInput]);

  if (!llmInput) {
    return EMPTY_LLM_STATE;
  }

  if (llmState.input !== llmInput) {
    return { input: llmInput, result: null, status: 'running', errorMessage: '' };
  }

  return llmState;
}
