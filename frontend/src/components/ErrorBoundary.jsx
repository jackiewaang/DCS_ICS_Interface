import { Component } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default class ErrorBoundary extends Component {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, info) {
    console.error('Unexpected frontend error:', error, info);
  }

  render() {
    if (!this.state.hasError) return this.props.children;

    return (
      <main className="flex min-h-screen items-center justify-center bg-background p-6">
        <section role="alert" className="w-full max-w-lg rounded-xl border border-destructive/30 bg-card p-8 text-center shadow-sm">
          <AlertTriangle className="mx-auto h-9 w-9 text-destructive" />
          <h1 className="mt-4 text-xl font-semibold text-foreground">The application could not display this page</h1>
          <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
            An unexpected interface error occurred. Reload the application to recover.
          </p>
          <Button type="button" onClick={() => window.location.reload()} className="mt-6">
            <RefreshCw className="h-4 w-4" />
            Reload application
          </Button>
        </section>
      </main>
    );
  }
}
