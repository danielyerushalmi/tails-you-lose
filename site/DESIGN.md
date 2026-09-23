# Tails, You Lose — design doc (authoritative for the site)

## Concept
A research site for the study "Do AI models inherit human money biases?". The visitor
takes the same seven tests the models took, then sees their own answers placed next to
humans (classic literature) and ten local AI models. The hero is a pile of minted coins
on a dark banker's-desk panel; the cursor shoves them, a click flips one.

## Derivation (lusion skill, "Deriving your own direction")
1. Name → mood → material world. "Tails, you lose" (the rigged bet) → *wager, ledger,
   deadpan* → an accountant's ledger book: pale green ruled paper, red and green ruling,
   brass coins, rubber stamps, carbon copies, tabular figures.
2. Temperature: cool-green (ledger paper), NOT warm cream (Daniel's portfolio already
   owns cream + orange) and not graphite (Sunder).
3. Tinted neutrals. Paper is ledger green-white, ink is bottle-green black.
4. Accent with a semantic alibi: LEDGER RED. It is the ink accountants use for losses
   ("in the red"). The whole study is about how minds overweight losses.
5. Accent budget < 2%: loss figures, the tails side, one ruled margin line, pill dots.
6. Copy voice: deadpan bookkeeping. Entries, debits, audits. Numbers are objects.
7. Signature interaction from the name: flip the coin.
8. Positioned against presets: light page with dark panels (like A), cold-green not lavender,
   instrument-style tests (not a long scroll story).
9. Borrowed mechanics only: physics pile in a framed panel (lusion.co), masked line reveals.
   Re-costumed as coins on a desk blotter; utility layer in monospace like a ledger printout.

## Tokens
```
--paper:   oklch(95.5% 0.018 150)   ledger paper
--paper-2: oklch(92.5% 0.024 152)   ruled card
--rule:    oklch(80% 0.05 175 / .5) ledger ruling
--ink:     oklch(22% 0.025 165)     bottle-green black
--panel:   oklch(19% 0.03 165)      desk blotter (3D lives here)
--red:     oklch(54% 0.2 27)        loss ink (accent)
```
Type: Schibsted Grotesk 400/500 (display + body) · Geist Mono (utility layer, figures).

## Chapters
0. Hero — panel with physics coins; "Tails, you lose." + one-line finding.
1. Ledger summary — the three big numbers + the headline result.
2. Seven entries — each: scenario card → visitor answers → reveal (you · humans · 10 models).
3. The audit — Bias Quotient table (models × biases), visitor row inserted, toggles.
4. Findings — scaling, contamination (classic vs novel), deliberation, advisor persona.
5. Who you decide like — nearest model.
6. Paper + method + footer.

## Rules
Light page. No neon, no gradients-on-text, no em dashes in copy, no bounce easing.
Every section responds to the pointer.
