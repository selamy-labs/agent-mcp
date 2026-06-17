# When a capability should be an MCP server vs a skill

Short, grounded heuristic for deciding where a new agent capability belongs:
the public **`agent-mcp`** repo (this one) or the public **`agent-skills`** repo.

## The distinction

- A **skill** is *procedural know-how*: instructions, conventions, and judgment
  the model already has the tools to execute. It changes **how the model thinks
  and what steps it takes**. It ships as Markdown, costs nothing at runtime, and
  is only as reliable as the model following it.
- An **MCP server** is a *typed tool integration*: deterministic code the model
  **calls** and gets an exact result back from. It changes **what the model can
  actually do**, not just how it reasons. It ships as code, runs out-of-process,
  and is as reliable as the code.

## Make it an MCP server when

- **The operation must be exact / deterministic.** Hashing, encoding, byte math,
  timezone conversion, JSON canonicalization — anything where a model doing it
  "by hand" is silently wrong some fraction of the time. (This is exactly the
  `datakit` server in this repo.)
- **It touches an external or authed API.** Typed inputs/outputs, credential
  handling, pagination, and rate limits belong in code, not in a prompt.
- **It is stateful or has side effects.** Reads/writes to a store, a queue, a
  filesystem, a ticket system. The contract and the failure modes need to be
  real, not described.
- **The result needs to be verifiable and reproducible.** A tool returns a value
  you can assert on in tests; prose guidance cannot be unit-tested.

## Make it a skill when

- **It is judgment, process, or convention.** "Verify the real artifact before
  claiming done", "model a REST resource this way", "scrub cross-org names" —
  there is no API call, only a better way to use the tools you already have.
- **It composes existing tools.** If the value is *which* tools to call and in
  *what order* under *what conditions*, that is a skill orchestrating tools an
  MCP server (or the base harness) already provides.
- **It is mostly natural-language reasoning.** Summarizing, classifying,
  rewriting, planning — the model is the engine; a skill just steers it.

## The litmus test

> If you could write a passing unit test for the capability, it probably wants to
> be an **MCP tool**. If the "test" would be a human judging whether the agent
> *behaved well*, it probably wants to be a **skill**.

Many real capabilities are a **pair**: a deterministic MCP server for the
mechanics plus a thin skill describing when and how to wield it well. That is the
intended relationship between this repo and `agent-skills`.
