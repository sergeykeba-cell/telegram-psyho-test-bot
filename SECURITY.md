# Security Policy

## Scope

This repository contains a Telegram bot, a Mini App and an n8n workflow for psychological screening questionnaires.
It is a research and workflow tool, not a medical device. Screening results are not diagnoses.

## Reporting a vulnerability

Please use GitHub private vulnerability reporting (Security tab, "Report a vulnerability").
Do not open a public issue for security problems.

Never include real patient data, names, Telegram IDs, session tokens, `.env` contents or n8n credentials in a report,
an issue or a pull request. Use synthetic data only.

## Supported versions

Only the current `main` branch is maintained.

## What is not published here

Secrets, credentials, chat IDs and production hostnames are intentionally not part of this repository.
The workflow export is sanitized; see `DEPLOYMENT.md` for the export procedure.
