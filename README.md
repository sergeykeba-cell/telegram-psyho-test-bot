<!-- readme-v2 -->
# PsyhoTestBot

A Telegram bot for a psychologist plus a Telegram Mini App for patients. The doctor creates a one-time
test session (link and QR code), the patient answers a screening instrument on their phone, and the
doctor receives the result in Telegram: a summary, per-item answers and a PDF report.

> **Status: not for use with real patients yet.** Open items: the Mini App is not verified on real
> phones, the crisis hotline numbers are not confirmed by calling them, failure alerts to the
> administrator are not verified end to end, and the clinical content (translations, thresholds,
> scoring keys) has had no specialist review. See [Known limitations](#known-limitations).

## Instruments (15)

All Ukrainian-language texts are working translations and are **not validated**. Thresholds marked
"unverified" are implemented from memory in the code and were not checked against the primary source.

| Key | Instrument | Items | Scoring and status |
| --- | --- | --- | --- |
| `pcl5` | PCL-5 (PTSD) | 20 | Sum 0-80; screening cutoff 31-33 and the DSM-5 provisional rule are unverified |
| `phq9` | PHQ-9 (depression) | 9 | Bands 5/10/15/20; item 9 above zero raises a crisis flag regardless of the sum |
| `gad7` | GAD-7 (anxiety) | 7 | Bands 5/10/15; cutoff 10 unverified |
| `minmult` | Mini-Mult (short MMPI) | 71 | Yes/No; K-corrected scales; T-scores need the patient's sex; key taken from a methodological PDF, **not** checked against Kozyulya (1994) |
| `schmishek` | Schmishek (accentuations) | 88 | 10 Leonhard scales; accentuation above 19, tendency 15-19; sources disagree |
| `isi` | ISI (insomnia) | 7 | Sum 0-28; bands 8/15/22 unverified; one uniform answer scale instead of the original per-item labels |
| `phq15` | PHQ-15 (somatic symptoms) | 15 | Sum 0-30; bands 5/10/15 unverified; item 4 is skipped for male patients |
| `pss10` | PSS-10 (perceived stress) | 10 | Reverse items 4, 5, 7, 8; no official clinical cutoffs, the 13/26 bands are conventional |
| `who5` | WHO-5 (well-being) | 5 | Raw sum times 4 (0-100); 50 and 28 thresholds unverified |
| `nsi` | NSI (post-concussion) | 22 | Sum 0-88; no clinical cutoffs; sub-groups are conventional |
| `brief_cope` | Brief COPE (coping) | 28 | 14 subscales of two items (0-6); no total score and no cutoffs |
| `audit_c` | AUDIT-C (alcohol) | 3 | Sum 0-12; 4 for men and 3 for women; needs the patient's sex |
| `audit` | AUDIT (alcohol) | 10 | Sum 0-40; zones 8/16/20 unverified; items 9-10 are scored 0/2/4 |
| `c_ssrs` | C-SSRS screener | 6 | Items 3-5 are asked only if item 2 is Yes; risk triage unverified |
| `express` | Combined express screening | 26 | PHQ-9 + GAD-7 + ISI + AUDIT-C, one level per scale, no total score |

## How it works

```
patient phone -- Mini App (nginx) --> n8n webhooks --> PostgreSQL
                                          |
                                          +--> bot /result (X-Webhook-Secret) --> doctor in Telegram
```

1. The doctor creates a session in the bot. The bot stores a one-time token and sends a link and a QR code.
2. The Mini App loads the session (`GET /webhook/session`) and posts the answers (`POST /webhook/psychotest`).
3. n8n validates every answer value strictly (empty, non-numeric or out-of-range values are errors),
   computes the score in the `JS: Scoring1` node, stores the result and notifies the bot.
4. The bot sends the doctor a summary with buttons for per-item answers and a PDF.
5. Results have a `status` of `scored` and then `notified`. A scheduled n8n branch in `workflow.json` re-sends
   results that are still `scored` every five minutes, with a limit of 12 attempts and an administrator alert
   when the limit is reached. Check that your deployed workflow matches the file.

Crisis handling: the Mini App shows a support screen once per session when PHQ-9 item 9 or the combined
screening item 9 is above zero, or when any C-SSRS answer is positive. The doctor sees a red flag and a
button that assigns a C-SSRS session to the same patient. Contact numbers live in `CRISIS_CONTACTS` in
`index.html` and are **not verified**.

## Configuration

Copy `.env.example` to `.env` and fill in: `BOT_TOKEN`, `DATABASE_URL`, `MINI_APP_URL`, `WEBHOOK_HOST`,
`WEBHOOK_PORT`, `WEBHOOK_SECRET`, `ADMIN_TG_ID`. The bot refuses to start with an empty `WEBHOOK_SECRET`.
Never commit `.env` or a raw n8n export.

## Quick start

Requires Python 3.12 and the services described in [DEPLOYMENT.md](DEPLOYMENT.md).

```bash
python3 -m venv venv
venv/bin/pip install -r requirements.txt
```

## Files

| Path | Purpose |
| --- | --- |
| `bot.py` | Telegram bot (aiogram 3.7) and the aiohttp endpoint that receives results from n8n |
| `report.py` | PDF reports (reportlab) and the per-item answer lists used by the bot |
| `index.html` | Patient Mini App: one static file with all test definitions, served by nginx |
| `questions.json` | Snapshot of questions and answer options used for per-item reports |
| `workflow.json` | Sanitized n8n export: validation, scoring, storage, notification, retry |
| `error_handler.json` | n8n workflow that reports failures of the main workflow |
| `schema.sql` | PostgreSQL schema |
| `requirements.txt` | Pinned Python dependencies (Python 3.12) |
| `.env.example` | Environment variables (no real values) |
| `smoke_pdf.py` | Generates a sample PDF per test for a visual check |
| `snap/` | Reference snapshots used by the smoke check |
| `DEPLOYMENT.md` | Production setup: Docker, n8n, PostgreSQL, nginx, systemd |
| `QUICKSTART.md` | Pointer to DEPLOYMENT.md |
| `SECURITY.md` | Security policy and how to report a problem |

## Known limitations

- Not validated for clinical use: translations, thresholds and scoring keys need review by a specialist.
- The Mini-Mult key and the Schmishek "Pedantry" key differ between sources; the repository follows the
  source named in the scoring code comments. The T-score formula is not checked against the original.
- Rights to the test texts and keys have not been assessed.
- The one-time session link is sent to a third-party QR service (api.qrserver.com); it contains the token,
  not the patient's name.
- Patient names and answers are stored in PostgreSQL; protect the server, the database and the backups accordingly.
- `report.py` contains several overlapping definitions of the per-item helpers; the last definition wins.

## License

No license is granted. All rights are reserved by default.
