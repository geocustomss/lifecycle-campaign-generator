# Demo and screenshot plan

## 1. Record a GIF / Loom of the whole flow
```bash
bash demo.sh       # prints each command, pauses, runs it (PAUSE=0 bash demo.sh for an instant run)
```
Record it with any of: Loom (also good for the walkthrough video), [asciinema](https://asciinema.org) + `agg` to make a GIF,
[ScreenToGif](https://www.screentogif.com) (Windows) or [Kap](https://getkap.co) (macOS). Terminal tips: dark theme,
font size 18+, ~100 columns wide, short prompt (`export PS1='$ '`), and no personal paths or API keys on screen.

## 2. Hero screenshot
Capture the segment table plus the 'blocked [at_risk/urgency]: forbidden claim' line.

Save as `docs/demo.png` (or `docs/demo.gif`) and add this under the first paragraph of the README:
```markdown
![demo](docs/demo.gif)
```

## 3. Things to point at while narrating
- Six segments from recency/frequency/spend rules.
- The compliance gate disqualifies a variant even when it scores well.
- The plan respects email/SMS opt-in and assigns A/B arms deterministically.

## 4. Before you publish
Re-run with a real model, then pick one real rendered email and SMS to show in the README.
