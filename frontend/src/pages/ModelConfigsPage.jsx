import { Braces, Database, Loader2 } from "lucide-react";

const FIELD_LABELS = {
  config_id: "Configuration ID",
  name: "Name",
  emb_model: "Embedding model",
  run_mode: "Run mode",
  fusion_type: "Fusion type",
  normalise_emb: "Normalize embeddings",
  normalise_case_feats: "Normalize case features",
  case_feat_names: "Case features",
  label_config: "Label configuration",
  model_path: "Model artifact",
  scaler_path: "Scaler artifact",
};

function fieldLabel(key) {
  return FIELD_LABELS[key] || key.replaceAll("_", " ");
}

function ModelValue({ value }) {
  if (value === null || value === undefined || value === "") {
    return <span className="italic text-muted-foreground">Not specified</span>;
  }

  if (typeof value === "boolean") {
    return <span>{value ? "Yes" : "No"}</span>;
  }

  if (Array.isArray(value)) {
    if (value.length === 0) {
      return <span className="italic text-muted-foreground">None</span>;
    }

    return (
      <div className="flex flex-wrap gap-1.5">
        {value.map((item) => (
          <span
            key={String(item)}
            className="rounded-full border border-border bg-secondary px-2 py-0.5 text-xs text-secondary-foreground"
          >
            {String(item)}
          </span>
        ))}
      </div>
    );
  }

  if (typeof value === "object") {
    return (
      <pre className="max-h-52 overflow-auto whitespace-pre-wrap rounded-md bg-muted p-3 font-mono text-xs leading-relaxed text-foreground">
        {JSON.stringify(value, null, 2)}
      </pre>
    );
  }

  return <span className="break-all">{String(value)}</span>;
}

export default function ModelConfigsPage({ models, isLoading, error }) {
  return (
    <div className="mx-auto w-full max-w-7xl space-y-6 p-6 md:p-8">
      <header className="space-y-2 border-b border-border pb-5">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <Database className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-foreground md:text-[2rem]">
              Model Configurations
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Classification models currently registered by the analysis service.
            </p>
          </div>
        </div>
      </header>

      {isLoading && (
        <div className="flex min-h-64 items-center justify-center rounded-xl border border-border bg-card">
          <div className="flex items-center gap-3 text-sm text-muted-foreground">
            <Loader2 className="h-5 w-5 animate-spin text-primary" />
            Loading model configurations…
          </div>
        </div>
      )}

      {!isLoading && error && (
        <div role="alert" className="rounded-xl border border-destructive/30 bg-destructive/10 p-5 text-sm text-destructive">
          {error}
        </div>
      )}

      {!isLoading && !error && models.length === 0 && (
        <div className="rounded-xl border border-border bg-card p-8 text-center">
          <Braces className="mx-auto h-8 w-8 text-muted-foreground" />
          <p className="mt-3 text-sm text-muted-foreground">No model configurations are registered.</p>
        </div>
      )}

      {!isLoading && !error && models.length > 0 && (
        <div className="grid gap-6 xl:grid-cols-2">
          {models.map((model) => (
            <article key={model.config_id} className="overflow-hidden rounded-xl border border-border bg-card shadow-sm">
              <div className="border-b border-border bg-secondary/60 px-5 py-4">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                      Configuration {model.config_id}
                    </p>
                    <h2 className="mt-1 text-lg font-semibold text-foreground">
                      {model.name || "Unnamed model"}
                    </h2>
                  </div>
                  <span className="rounded-full bg-primary px-2.5 py-1 text-xs font-semibold text-primary-foreground">
                    {model.run_mode || "Unspecified"}
                  </span>
                </div>
              </div>

              <dl className="divide-y divide-border">
                {Object.entries(model).map(([key, value]) => (
                  <div key={key} className="grid gap-2 px-5 py-3 sm:grid-cols-[11rem_minmax(0,1fr)]">
                    <dt className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                      {fieldLabel(key)}
                    </dt>
                    <dd className="min-w-0 text-sm text-foreground">
                      <ModelValue value={value} />
                    </dd>
                  </div>
                ))}
              </dl>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
