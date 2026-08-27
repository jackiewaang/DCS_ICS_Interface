import { useState } from "react";
import { CheckCircle2, MessageSquare, Send, Star } from "lucide-react";

import { Button } from "@/components/ui/button";
import { api } from "@/services/api";

const MAX_MESSAGE_LENGTH = 5000;

export default function FeedbackPage() {
  const [rating, setRating] = useState(0);
  const [message, setMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [isSubmitted, setIsSubmitted] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    const cleanMessage = message.trim();

    if (!rating || !cleanMessage) {
      setError("Choose a rating and add a short message.");
      return;
    }

    setIsSubmitting(true);
    setError("");
    setIsSubmitted(false);

    try {
      await api.submitFeedback({ rating, message: cleanMessage });
      setRating(0);
      setMessage("");
      setIsSubmitted(true);
    } catch (err) {
      setError(err.message || "Feedback could not be submitted. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-full items-center justify-center p-6 md:p-8">
      <section className="w-full max-w-xl rounded-xl border border-slate-200 bg-white p-6 shadow-sm md:p-8">
        <div className="mb-6 flex h-11 w-11 items-center justify-center rounded-full bg-slate-100">
          <MessageSquare className="h-5 w-5 text-slate-600" />
        </div>

        <h1 className="text-2xl font-semibold text-slate-950">Share your feedback</h1>
        <p className="mt-2 text-sm leading-relaxed text-slate-500">
          Tell us what works well or what would make the system more useful.
        </p>

        <form className="mt-7 space-y-6" onSubmit={handleSubmit}>
          <fieldset>
            <legend className="text-sm font-medium text-slate-800">Overall experience</legend>
            <div className="mt-3 flex gap-2">
              {[1, 2, 3, 4, 5].map((value) => (
                <button
                  key={value}
                  type="button"
                  aria-label={`${value} out of 5 stars`}
                  aria-pressed={rating === value}
                  onClick={() => {
                    setRating(value);
                    setError("");
                    setIsSubmitted(false);
                  }}
                  className={`cursor-pointer rounded-md border p-2 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400 ${
                    value <= rating
                      ? "border-amber-300 bg-amber-50 text-amber-500"
                      : "border-slate-200 text-slate-300 hover:border-slate-300 hover:text-slate-400"
                  }`}
                >
                  <Star className={`h-5 w-5 ${value <= rating ? "fill-current" : ""}`} />
                </button>
              ))}
            </div>
          </fieldset>

          <div>
            <label htmlFor="feedback-message" className="text-sm font-medium text-slate-800">
              Your feedback
            </label>
            <textarea
              id="feedback-message"
              value={message}
              maxLength={MAX_MESSAGE_LENGTH}
              rows={6}
              placeholder="What should we keep, change, or improve?"
              onChange={(event) => {
                setMessage(event.target.value);
                setError("");
                setIsSubmitted(false);
              }}
              className="mt-3 w-full resize-y rounded-md border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-900 shadow-xs outline-none placeholder:text-slate-400 focus:border-slate-400 focus:ring-2 focus:ring-slate-200"
            />
            <p className="mt-1.5 text-right text-xs text-slate-400">
              {message.length.toLocaleString()} / {MAX_MESSAGE_LENGTH.toLocaleString()}
            </p>
          </div>

          {error && (
            <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
              {error}
            </p>
          )}

          {isSubmitted && (
            <p role="status" className="flex items-center gap-2 rounded-md bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
              <CheckCircle2 className="h-4 w-4" />
              Thank you. Your feedback has been submitted.
            </p>
          )}

          <Button type="submit" disabled={isSubmitting} className="w-full bg-slate-700 hover:bg-slate-800">
            <Send className="h-4 w-4" />
            {isSubmitting ? "Submitting…" : "Submit feedback"}
          </Button>
        </form>
      </section>
    </div>
  );
}
