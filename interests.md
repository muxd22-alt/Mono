# Interest Profile — Mono Signal OS

This is the only file you should need to hand-edit as your interests shift.
The scorer reads it on every run and judges new inbox items against it —
change a line here and every future score reflects it immediately.

## 🔵 Financial & Market Intelligence

- Early signals of stock market stress or crashes: unusual volatility,
  credit spread widening, forced-selling patterns, correlated drawdowns
  across asset classes.
- TASI (Saudi stock market) movements, sector rotations, and quant
  signals — anything that would affect the TASI Quant Replicator.
- Economic cycle turns relevant to timing decisions: rate-cut or
  rate-hike signals, yield curve moves, anything that would change
  a buy / sell / DCA decision on stocks or crypto.
- Crypto regime shifts: Bitcoin halving cycle effects, liquidity
  expansions, regulatory moves, on-chain anomalies.
- SAMA (Saudi Central Bank) policy: DBR changes, restructuring rules,
  mortgage regulation shifts.

## 🟣 AI / Research / AGI

- The word "AGI" or "ASI" appearing in a new context: a paper, a lab
  announcement, a policy document, or a shift in how often it shows up
  in arXiv abstracts or mainstream coverage.
- Breakthroughs in agentic AI: new agent frameworks, tool-use
  capabilities, autonomous coding, multi-agent orchestration.
- AI model releases that change the capability frontier: new reasoning
  models, multimodal systems, open-weight releases.
- Bioinformatics + AI intersections relevant to ClawBio.

## 🟢 Saudi Economy / Urban / Labour

- Employment and AI intersecting: layoffs attributed to automation,
  hiring freezes in roles exposed to AI tooling, new benchmarks on
  job displacement.
- Saudi Vision 2030 economic indicators, urban heat island data,
  post-labour economy signals.
- Agricultural technology and food security developments in the
  Gulf region.

## 🟠 Products & Platforms

- Hudhud platform developments, PWA best practices, service worker
  patterns for offline-first apps.
- New approaches to personal AI assistants (moltis, PAI), local-first
  AI, Rust-based systems.
- Telegram bot frameworks and conversational AI patterns.

## 🔴 Mobile & Infrastructure

- Termux / Android native development breakthroughs, proot-free
  approaches, single-binary deployments.
- Mesh networking, peer-to-peer VPN, DNS sinkhole ad-blocking
  advances.
- Edge computing and on-device ML inference.

## 🟡 News & Dashboards

- Geopolitical signals that affect markets: energy policy, trade
  tensions, sanctions, regional conflicts.
- Intelligence pipeline architecture patterns, news aggregation
  at scale, automated OSINT.

## What counts as a breakthrough (vs. routine)

This is what the scorer checks "novelty" against. Vague relevance is
not enough — score novelty high only when the item clears the bar
below for its category, and low when it's a routine restatement of
something already known.

- **Financial & market**: a spread, correlation, or volatility level
  breaking a multi-year pattern; a rate surprise vs. consensus. Not:
  routine daily moves, expected earnings, expected rate decisions.
- **AI / research / AGI**: a capability that didn't exist last month —
  a benchmark broken by a wide margin, a lab claiming a genuine first,
  AGI/ASI used by a source that's never used it before. Not: another
  incremental model release, another post restating known ideas.
- **Saudi economy / urban / labour**: an actual policy change, not a
  policy discussion; a number breaking a multi-year trend. Not:
  routine indicator releases in line with expectations.
- **Products & platforms**: a pattern or tool you haven't seen
  implemented before, or one that solves your exact problem. Not:
  another tutorial on something you already know.
- **Mobile & infrastructure**: a way to do something on your stack
  (Termux, mesh networking) that was previously painful or impossible.
  Not: an incremental version bump.
- **News & geopolitics**: an event that changes the odds of a
  market-moving outcome. Not: continuation of an already-priced-in
  situation.

## Scoring guidance

- Urgency 9-10: actionable today — a signal that would change a
  decision if you saw it tomorrow instead of now.
- Urgency 5-8: worth reading, fits a daily digest, not time-critical.
- Urgency 1-4: tangential or already-known — low relevance or novelty.
- Novelty is graded against the breakthrough bar above, and also
  against what's already been filed recently (the scorer shows the
  model your last ~15 entries so it doesn't re-flag the same thing
  as a breakthrough twice).

Edit the themes above freely. Nothing else in the pipeline needs to
change when you do.
