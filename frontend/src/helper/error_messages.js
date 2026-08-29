export function getUserErrorMessage(error, fallback = 'Something went wrong. Please try again.') {
  if (error?.name === 'AbortError') {
    return 'The request was cancelled before it completed.';
  }

  if (error instanceof TypeError && /fetch|network|load/i.test(error.message || '')) {
    return 'Could not connect to the analysis service. Check your connection and try again.';
  }

  if (error instanceof TypeError || error instanceof SyntaxError) {
    return fallback;
  }

  const message = typeof error?.message === 'string' ? error.message.trim() : '';
  return message || fallback;
}
