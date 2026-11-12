# poc-ai-code-test-coverage

**The question:** when a coding agent writes a module *and its own tests*, what do
those tests actually verify — and does mutation testing close the gap?

**The answer:** the agent's suite scored **100% line coverage but only 90.67%
mutation score** — seven code changes no test caught, clustered exactly where you'd
predict: boundaries, tie-breaks, and cross-rule interactions. One mutation-guided
feedback round fixed six of the seven (**98.67%**), and the agent correctly proved
the seventh mutant *equivalent* — unkillable by any test — rather than writing a
junk test to chase the score.

> Exploratory PoC, throwaway by default. Written up in
> [Your AI's tests pass. Here's what they don't check](https://garyparker.dev/blog/mutation-testing-ai-generated-tests).

## Method

A coding agent (Claude Code, headless `claude -p`) was given [`SPEC.md`](SPEC.md) —
a voucher/discount engine with deliberately boundary-rich rules (min-spend `>=`,
expiry-inclusive dates, half-up rounding, discount caps, stacking, duplicate codes)
— and asked to implement the module **and write the test suite it considered
production-complete**. No mention of mutation testing in the brief; this measures
default agent behaviour.

Then:

1. **Measure** — line coverage (Vitest v8) and mutation score (StrykerJS).
2. **Feed back** — give the agent the surviving mutants, ask it to strengthen the
   tests. Source and configs locked; tests only.
3. **Re-measure.**

## Results

| | Round 1 (agent defaults) | Round 2 (mutation-guided) |
|---|---|---|
| Tests | 31 | 37 |
| Line coverage | **100%** | 100% |
| Branch coverage | 95.8% | 100% |
| Mutation score | **90.67%** (7 survived of 75) | **98.67%** (1 survived) |
| Agent time | 2m 47s | ~3m |

## What the seven survivors were

Every survivor maps to a real defect class that 100% line coverage waved through:

| Mutant | The defect it represents |
|---|---|
| `price < 0` → `price <= 0` | Zero-price items (freebies) start throwing — no test used a zero price |
| Error message → `""` (×2) | Exceptions asserted by type only; messages never verified |
| `if (v.stackable) continue` → `if (false)` | Stackable vouchers silently join the "best non-stackable" race — no test had a stackable out-discounting a non-stackable |
| `discount > best` → `if (true)` | Last eligible voucher always wins instead of the best one |
| `>` → `>=` | Tie between equal vouchers flips to the later code |
| min-spend clause → `true` | **Equivalent mutant** — provably unkillable (see below) |

## The two findings that matter

**1. Coverage measured what the tests execute. Mutation measured what they verify.**
The agent's default suite was genuinely good — 31 tests, sensible structure, all
green, perfect coverage. The discourse says AI tests cover "about half" the failure
space; here it was better than that (90.67%), but the missing 9% was precisely the
high-value part: boundary conditions and rule interactions — where production
incidents live.

**2. The feedback loop works, including the hard part.** Given the survivors, the
agent wrote six targeted tests named after the defect each mutant represents. And
for the seventh it did equivalent-mutant analysis: the mutation replaces `X` in
`X && Y` with `true`, but when `X` is false, `Y` is `subtotal < undefined` — always
false in JS, so behaviour is identical for every input. It proved this empirically,
declined to write a fake test, and recommended a `// Stryker disable` annotation.
Equivalent-mutant triage is the reason teams abandon mutation testing; the agent
handled it unprompted.

## Caveats

- One module, one agent, one run — indicative, not a benchmark.
- The spec was written to be boundary-rich; blander code would show a smaller gap.
- TypeScript was pinned to 5.8 (Stryker's tsconfig preprocessor doesn't yet handle
  the TS 7 preview npm now installs by default).

## Reproduce

```bash
npm ci
npx vitest run --coverage   # 37 tests, 100% line coverage
npx stryker run             # 98.67% mutation score, 1 equivalent survivor
```

The committed suite is the round-2 state (37 tests). Round-1 numbers come from
the run logs; to approximate the before state, delete the six tests whose names
reference mutants/tie-breaks/zero-price and re-run Stryker.

MIT. Public demo spec — no real pricing logic from anywhere.
