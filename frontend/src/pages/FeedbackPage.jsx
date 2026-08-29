import { useState } from "react";
import { CheckCircle2, MessageSquareText, Send } from "lucide-react";

import { Button } from "@/components/ui/button";
import { api } from "@/services/api";

const MAX_COMMENTS_LENGTH = 5000;
const LIKERT_VALUES = [1, 2, 3, 4, 5];
const INITIAL_FEEDBACK = {
  tool_usefulness: 0,
  score_reasonability: 0,
  ease_of_use: 0,
  identified_improvements: "",
  comments: "",
};

function LikertQuestion({ id, label, lowLabel, highLabel, value, onChange }) {
  return (
    <fieldset className="py-6 first:pt-0">
      <legend className="text-sm font-semibold text-foreground">{label}</legend>
      <div className="mt-4 grid grid-cols-5 gap-2" role="group" aria-label={label}>
        {LIKERT_VALUES.map((option) => (
          <button
            key={option}
            type="button"
            aria-label={`${label}: ${option} out of 5`}
            aria-pressed={value === option}
            onClick={() => onChange(id, option)}
            className={`h-11 cursor-pointer rounded-md border text-sm font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ${
              value === option
                ? "border-primary bg-primary text-primary-foreground"
                : "border-border bg-background text-foreground hover:border-ring hover:bg-secondary"
            }`}
          >
            {option}
          </button>
        ))}
      </div>
      <div className="mt-2 flex justify-between gap-4 text-xs text-muted-foreground">
        <span>{lowLabel}</span>
        <span className="text-right">{highLabel}</span>
      </div>
    </fieldset>
  );
}

export default function FeedbackPage() {
  const [feedback, setFeedback] = useState(INITIAL_FEEDBACK);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [isSubmitted, setIsSubmitted] = useState(false);

  const updateFeedback = (field, value) => {
    setFeedback((current) => ({ ...current, [field]: value }));
    setError("");
    setIsSubmitted(false);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (
      !feedback.tool_usefulness
      || !feedback.score_reasonability
      || !feedback.ease_of_use
      || !feedback.identified_improvements
    ) {
      setError("Please answer all rating and improvement questions before submitting.");
      return;
    }

    setIsSubmitting(true);
    setError("");
    setIsSubmitted(false);

    try {
      await api.submitFeedback({
        ...feedback,
        comments: feedback.comments.trim() || null,
      });
      setFeedback(INITIAL_FEEDBACK);
      setIsSubmitted(true);
    } catch (err) {
      setError(err.message || "Feedback could not be submitted. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-full w-full p-6 md:p-10">
      <div className="mx-auto w-full max-w-7xl">
        <header className="border-b border-border pb-6">
          <div className="flex items-start gap-4">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-secondary">
              <MessageSquareText className="h-5 w-5 text-secondary-foreground" />
            </div>
            <div>
              <h1 className="text-2xl font-semibold tracking-tight text-foreground md:text-[2rem]">
                Share your feedback
              </h1>
              <p className="mt-2 max-w-3xl text-sm leading-relaxed text-muted-foreground">
                Help us evaluate the usefulness, clarity, and reliability of the analysis.
              </p>
            </div>
          </div>
        </header>

        <form className="mt-8 grid gap-10 lg:grid-cols-[minmax(0,1fr)_minmax(22rem,0.8fr)]" onSubmit={handleSubmit}>
          <section aria-labelledby="ratings-heading">
            <h2 id="ratings-heading" className="text-lg font-semibold text-foreground">Evaluation</h2>
            <p className="mt-1 text-sm text-muted-foreground">Select one response from 1 to 5 for each statement.</p>

            <div className="mt-6 divide-y divide-border">
              <LikertQuestion
                id="tool_usefulness"
                label="How useful was the tool for reviewing the case?"
                lowLabel="1 — Not useful"
                highLabel="5 — Very useful"
                value={feedback.tool_usefulness}
                onChange={updateFeedback}
              />
              <LikertQuestion
                id="score_reasonability"
                label="How reasonable was the score provided by the tool?"
                lowLabel="1 — Not reasonable"
                highLabel="5 — Very reasonable"
                value={feedback.score_reasonability}
                onChange={updateFeedback}
              />
              <LikertQuestion
                id="ease_of_use"
                label="How easy was the tool to use?"
                lowLabel="1 — Very difficult"
                highLabel="5 — Very easy"
                value={feedback.ease_of_use}
                onChange={updateFeedback}
              />
            </div>
          </section>

          <section className="border-t border-border pt-8 lg:border-l lg:border-t-0 lg:pl-10 lg:pt-0" aria-labelledby="details-heading">
            <h2 id="details-heading" className="text-lg font-semibold text-foreground">Improvements and comments</h2>

            <fieldset className="mt-6">
              <legend className="text-sm font-semibold text-foreground">
                Did the tool help you identify improvements?
              </legend>
              <div className="mt-3 grid grid-cols-3 gap-2">
                {[["yes", "Yes"], ["somewhat", "Somewhat"], ["no", "No"]].map(([option, label]) => (
                  <button
                    key={option}
                    type="button"
                    aria-pressed={feedback.identified_improvements === option}
                    onClick={() => updateFeedback("identified_improvements", option)}
                    className={`h-11 cursor-pointer rounded-md border px-3 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ${
                      feedback.identified_improvements === option
                        ? "border-primary bg-primary text-primary-foreground"
                        : "border-border bg-background text-foreground hover:border-ring hover:bg-secondary"
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </fieldset>

            <div className="mt-8">
              <div className="flex items-baseline justify-between gap-4">
                <label htmlFor="feedback-comments" className="text-sm font-semibold text-foreground">Comments</label>
                <span className="text-xs text-muted-foreground">Optional</span>
              </div>
              <textarea
                id="feedback-comments"
                value={feedback.comments}
                maxLength={MAX_COMMENTS_LENGTH}
                rows={10}
                placeholder="Tell us what worked well, what seemed unclear, or what could be improved."
                onChange={(event) => updateFeedback("comments", event.target.value)}
                className="mt-3 min-h-56 w-full resize-y rounded-md border border-input bg-background px-3 py-3 text-sm leading-6 text-foreground shadow-xs outline-none placeholder:text-muted-foreground/70 focus:border-ring focus:ring-2 focus:ring-ring/20"
              />
              <p className="mt-1.5 text-right text-xs text-muted-foreground">
                {feedback.comments.length.toLocaleString()} / {MAX_COMMENTS_LENGTH.toLocaleString()}
              </p>
            </div>

            {error && (
              <p role="alert" className="mt-5 rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</p>
            )}

            {isSubmitted && (
              <p role="status" className="mt-5 flex items-center gap-2 rounded-md bg-success/10 px-3 py-2 text-sm text-success">
                <CheckCircle2 className="h-4 w-4" />
                Thank you. Your feedback has been submitted.
              </p>
            )}

            <Button type="submit" size="lg" disabled={isSubmitting} className="mt-6 w-full sm:w-auto cursor-pointer">
              <Send className="h-4 w-4" />
              {isSubmitting ? "Submitting…" : "Submit feedback"}
            </Button>
          </section>
        </form>
      </div>
    </div>
  );
}
