# TextGrad — notes

**Paper**: <https://arxiv.org/abs/2406.07496> (Yuksekgonul et al., 2024; Nature, 2025)
**Repo**: `~/code_ref/textgrad` (clone of <https://github.com/zou-group/TextGrad>)
**Tagline**: "Automatic 'differentiation' via text" — autograd engine for textual gradients.

## What it is

TextGrad treats LLM-produced critique strings as "gradients" and
propagates them backward through a computation graph. The API
deliberately mirrors PyTorch's autograd:

```python
import textgrad as tg
engine = tg.get_engine("gpt-4o")

prompt = tg.Variable("Initial prompt", role_description="A prompt")
loss_fn = tg.TextLoss("Critique the answer's correctness.")
optimizer = tg.TGD(parameters=[prompt])

for step in range(N):
    output = some_llm_pipeline(prompt)   # forward pass
    loss = loss_fn(output)               # textual loss
    loss.backward()                      # LLM produces gradient text
    optimizer.step()                     # LLM uses gradient to update prompt
```

`loss.backward()` calls an LLM that produces a *textual gradient* —
free-form feedback about how the upstream variable should change. The
optimizer step also calls an LLM to apply that feedback as a mutation.

## Why it's relevant

TextGrad is the precursor to GEPA's optimization framing. The conceptual
move — "use LLMs as gradient engines on text" — is identical. GEPA
extends this with:

- Pareto-aware multi-candidate evolutionary search (TextGrad is more
  like single-trace SGD).
- Cleaner trace-capture / reflection-dataset abstractions.
- More mature production tooling (`optimize_anything` API).

## When TextGrad over GEPA?

For our use-case (optimizing a single LLM-rewrite prompt against LiC
accuracy), GEPA's `optimize_anything` is the better fit:

- Easier API for "here's a candidate string, here's a scorer".
- Built-in Pareto search avoids local optima.
- Stronger production adoption (Databricks, Shopify, OpenAI).

TextGrad would shine if we wanted to optimize *multiple* interrelated
prompts in our pipeline (e.g., the analyzer's prompt AND the
rewriter's prompt as differentiable parameters of a joint loss). Not
the case tonight — we're optimizing the rewriter alone, holding the
analyzer constant.

## Takeaway

Skim and skip. GEPA subsumes the same mental model with a richer
optimizer.
