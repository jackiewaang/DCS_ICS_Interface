RANGE_DEFINITION = """
The historical REF GPA is a continuous score between 0.00 and 4.00.

Typical score ranges are:

3.50–4.00  : Outstanding
2.90–3.49  : Very considerable
2.00–2.89  : Considerable
0.00–1.99  : Recognised

These ranges are descriptive only.

Do not first select a category and then convert it to a score.

Instead, estimate the expected GPA directly.

Predictions should use the full continuous range.

For example, valid outputs include

3.08
3.27
3.46
2.18
2.73

and are not restricted to category midpoints.
"""


def build_score_prompt(summary: str, research: str, impact: str) -> str:
    return f"""
You are an expert assessor for the UK Research Excellence Framework (REF).

Assess the following REF Impact Case Study.

Use the REF definitions below.

{RANGE_DEFINITION}

Estimate the expected REF GPA.

The prediction should be any real number between 0.00 and 4.00.

Do not output a REF category.

Do not output Outstanding, Very considerable, Considerable or Recognised.

The prediction is a continuous value and should not be restricted to category midpoints.

Output exactly one number between 0.00 and 4.00.

Examples:
0.84
2.37
3.18
3.76

Output ONLY

x.xx

Do not provide any explanation.

Impact Case

Summary:
{summary}

Underpinning Research:
{research}

Details of Impact:
{impact}
"""


def build_diagnostic_prompt(
    score: float,
    summary: str,
    research: str,
    impact: str,
) -> str:
    return f"""
You are an expert UK REF impact assessor.

The impact case study has been predicted to receive a REF GPA of {score:.2f}.
Your task is to provide a concise, evidence-based explanation of that assessment
and identify the most useful ways the case could be strengthened.

Do NOT recalculate the GPA.
Do NOT invent evidence.
Use ONLY information contained in the case study.
Do NOT assume that missing quantitative evidence is necessarily a weakness.
Do NOT repeat the same weakness in different words.

{RANGE_DEFINITION}

==================================================
IMPACT CASE STUDY
==================================================

SUMMARY:
{summary}

UNDERPINNING RESEARCH:
{research}

DETAILS OF IMPACT:
{impact}

==================================================
OUTPUT
==================================================

Produce exactly the following structure.

1) CRITERIA ALREADY SATISFIED:
Write ONE or TWO sentences explaining why the case fits its predicted GPA
category. Identify the most important criteria/evidential characteristics
of that category that are already demonstrated, and briefly state what the
case actually demonstrates.

2) CRITERIA MISSING / COULD BE STRONGER:
Write THREE or FOUR sentences identifying the most important evidence that is
missing or insufficiently demonstrated for the case to be stronger within
its predicted category or, where appropriate, to support the next REF band.
Only identify a genuine and material weakness. If there is no important
missing criterion, say:
"No material evidential weakness is apparent from the case."

3) WEAK SENTENCES and IMPROVED VERSIONS:
Identify up to THREE sentences from the case that could materially weaken
the presentation of the impact case.

Choose sentences only when:
- the sentence makes an important impact claim that is insufficiently supported;
- the sentence is vague about an important evidential point;
- the sentence fails to connect existing evidence to the impact claim; or
- the sentence could be materially strengthened using evidence already present.

Do NOT select a sentence merely because its writing could be improved.
For every weak sentence identified above, provide a corresponding improved
version.

The improvement must:
- not just rewrite the same original sentence as the improved version;
- use ONLY evidence already present in the case;
- directly address the weakness identified;
- preserve the original factual meaning;
- make the smallest useful change;
- NOT add unrelated evidence simply to make the sentence longer;
- NOT invent or strengthen claims beyond the evidence.

Use this format:

a) "<EXACT ORIGINAL SENTENCE>"
   "<IMPROVED VERSION>"
b) "<EXACT ORIGINAL SENTENCE>"
   "<IMPROVED VERSION>"
c) "<EXACT ORIGINAL SENTENCE>"
   "<IMPROVED VERSION>"

If fewer than three sentences are genuinely problematic, provide fewer.
If none are materially problematic, write:
"None identified."

IMPORTANT:
The output must be concise.
Do not provide additional sections.
Do not provide a GPA recommendation.
Do not invent REF criteria that are not supported by the supplied definition.
"""
