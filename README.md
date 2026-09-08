# Daily attention engine

Drop this into a new (or existing) GitHub repo. Every issue you open
becomes an inbox item; the workflow scores it, alerts you on Telegram
if it's urgent, and files it as a numbered entry in the knowledge base.

## Setup

1. Create a new repo (private is fine) and copy these files in,
   keeping the folder structure (`.github/workflows/`, `scripts/`).
2. Edit `interests.md` to describe your actual themes - it already has
   a starting draft based on what you described.
3. Get an OpenRouter API key at openrouter.ai/keys. Add $10+ in credit
   to unlock the 1,000 requests/day tier (the `openrouter/free` router
   model itself costs $0 per request either way).
4. Create a Telegram bot via @BotFather, and get your own chat ID by
   messaging the bot once and checking
   `https://api.telegram.org/bot<token>/getUpdates`.
5. In the repo's Settings -> Secrets and variables -> Actions, add:
   - `OPENROUTER_API_KEY`
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
6. Open a test issue with a keyword or URL in the body. Within a
   minute or two you should see a comment on the issue with the score,
   the issue auto-closes, and `knowledge_base.jsonl` gets a new line.

## Files

- `interests.md` - the only file you should need to hand-edit as your
  interests shift. Read fresh on every scoring run.
- `.github/workflows/score-issue.yml` - fires on every new issue.
- `scripts/score_issue.py` - scores the item, routes urgent ones to
  Telegram, appends to the knowledge base, comments and closes the
  issue. Standard library only, nothing to install.
- `knowledge_base.jsonl` - created automatically on the first scored
  issue. One JSON object per line: id, timestamp, content, scores,
  summary. This is your permanent, ID-citable memory.

## Tuning

- `URGENCY_THRESHOLD` (default 9) - raise it if Telegram pings feel
  too frequent, lower it if things that should have pinged you didn't.
  Set it as a repo variable or edit the default in the script.
- `OPENROUTER_MODEL` (default `openrouter/free`) - the free router
  auto-picks a free model per request and filters for the features
  the request needs (e.g. image understanding for issues with a
  screenshot pasted in). Pin it to a specific `provider/model:free`
  slug instead if you want consistent behavior over speed of setup.

## Not built yet

The weekly digest that reads `knowledge_base.jsonl`, finds entries
related to the new one, and publishes a page via GitHub Pages - happy
to build that next once entries are actually accumulating.
