# Mono — Signal OS

Mono is an externalized attention and personal signal operating system. Every issue opened in this repository becomes an inbox item; GitHub Actions score it against your `interests.md` profile via OpenRouter, route urgent alerts directly to Telegram, classify items into 6 core pillars, and log them as permanent, numbered entries in `knowledge_base.jsonl`.

---

## ⚡ Key Features

- **6 Core Signal Pillars**:
  - 🔵 **Financial & Market Intelligence**: TASI quant signals, market stress/crash indicators, SAMA policy, macro yield curves, and crypto regime shifts.
  - 🟣 **AI / Research / AGI**: AGI/ASI tracking, frontier models, agentic frameworks, and bioinformatics (ClawBio).
  - 🟢 **Saudi Economy / Urban / Labour**: Vision 2030, Gulf labour trends, AI job displacement, Urban Heat Island (UHI) data, and food security.
  - 🟠 **Products & Platforms**: Hudhud platform, PWA architectures, PAI / Moltis assistants, and Telegram bot frameworks.
  - 🔴 **Mobile & Infrastructure**: Android/Termux native execution, proot-free tooling, mesh networking (WireGuard/Tailscale), and edge inference.
  - 🟡 **News & Dashboards**: Geopolitical OSINT, energy markets, intelligence pipelines, and real-time dashboard design.

- **Dual-Account Sensor Network**: Scans both `muxd22-alt` and `Muxd21` repositories daily, enriching each repo with pillar classifications, open issues, and activity metrics (`data/repos.json`).
- **Automated Morning Digest**: Summarizes 24h/7d interrupts, watch items, and active repos into `data/digest.json`.
- **Premium Web Dashboard**: Single-page application (`index.html`, `style.css`, `app.js`, `config.js`) supporting pillar filtering, quick capture, knowledge search, and GitHub Pages deployment.

---

## 🛠️ Architecture

```
Mono/
├── .github/workflows/
│   ├── score-issue.yml       # Scores opened issues, alerts Telegram, updates KB
│   └── daily-enrich.yml      # Daily repo scanning & daily digest generation
├── scripts/
│   ├── score_issue.py        # OpenRouter scoring, Telegram alerts, issue closing
│   ├── enrich_repos.py       # Scans muxd22-alt & Muxd21, enriches repos with metadata
│   └── daily_digest.py       # Summarizes recent signals and repository activity
├── data/
│   ├── repos.json            # Enriched GitHub repository metadata across pillars
│   └── digest.json           # Daily digest summary data
├── interests.md              # Live interest profile driving signal scoring
├── knowledge_base.jsonl      # Permanent, ID-citable memory database
├── config.js                 # Global dashboard configuration and repo-to-pillar map
├── index.html                # Signal OS Dashboard structure
├── style.css                 # Dark glassmorphism design system
└── app.js                    # Reactive frontend application logic
```

---

## 🔒 Required GitHub Secrets Setup

To enable automated scoring, Telegram alerts, and private/cross-account repository enrichment, add the following secrets under **Settings -> Secrets and variables -> Actions**:

1. `OPENROUTER_API_KEY`: Key from [OpenRouter](https://openrouter.ai/keys) to power model scoring (`openrouter/free` router or specified model).
2. `TELEGRAM_BOT_TOKEN`: Telegram bot token created via [@BotFather](https://t.me/BotFather).
3. `TELEGRAM_CHAT_ID`: Your personal or group Telegram Chat ID (obtain via `https://api.telegram.org/bot<token>/getUpdates`).
4. `GH_PAT`: Personal Access Token with `repo` scope to allow `scripts/enrich_repos.py` to fetch private/public repositories across both `muxd22-alt` and `Muxd21` accounts.

---

## 🚀 Getting Started

1. **Clone / Fork the Repository**:
   ```bash
   git clone https://github.com/muxd22-alt/Mono.git
   cd Mono
   ```

2. **Customize `interests.md`**:
   Update `interests.md` with your specific focus areas across any of the 6 pillars. The scorer reads this file on every run.

3. **Configure GitHub Secrets**:
   Set `OPENROUTER_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, and `GH_PAT` in your repo settings.

4. **Trigger a Signal**:
   Open a GitHub Issue in the repository with a URL, keyword, or note. Within 1-2 minutes:
   - The issue will be scored against `interests.md`.
   - A detailed scoring breakdown comment will be posted.
   - High-urgency items (Urgency ≥ 9) generate immediate Telegram alerts.
   - The item will be filed into `knowledge_base.jsonl` and auto-closed with a pillar label (`pillar:<Name>`).

5. **Deploy Dashboard**:
   Enable GitHub Pages in repo settings pointing to the `main` branch. The `daily-enrich.yml` workflow automatically updates `repos.json` and `digest.json` and deploys the dashboard daily at 04:00 UTC.
