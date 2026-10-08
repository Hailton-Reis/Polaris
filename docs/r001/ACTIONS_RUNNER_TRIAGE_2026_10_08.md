# GitHub Actions runner triage — Polaris / R001 — 2026-10-08

## Exact observed incident (not an application build failure)

- Repository: `Hailton-Reis/Polaris` (private), branch `r001/multisource-foundation`.
- `Issue 002 Android build gate`: [run 37825863641](https://github.com/Hailton-Reis/Polaris/actions/runs/37825863641), job [113478438938](https://github.com/Hailton-Reis/Polaris/actions/runs/37825863641/job/113478438938).
- Recorded GitHub REST fields: `conclusion=failure`, `steps=[]`, `runner_id=0`, `runner_name=""`, `runner_group_id=0`; job lasted ~2 seconds. The job did **not** execute even `actions/checkout`.
- `Domain spikes` has independently shown the same no-runner/no-step behavior; this affects two separate workflows, not just Android build steps.
- GitHub REST workflow run metadata lists a real workflow name/path, completed state and failure conclusion. This is **not** the distinct `BuildFailed` + `startup_failure` + zero-jobs case sometimes discussed online.
- Neither root cause, payment status, account standing, nor organization policy is accessible from the currently connected repository API. **Do not claim a specific cause.**

## Owner-side checks in recommended order

1. Open the [failed run](https://github.com/Hailton-Reis/Polaris/actions/runs/37825863641), expand its job and check for a banner above its empty logs. Capture the **exact GitHub message** (for example a runner assignment, spending limit, or payment notice). Do not paste payment details, tokens or screenshots with private information into issues.
2. Check the owner's [GitHub Billing overview](https://github.com/settings/billing), then **Budgets and alerts**, Actions included-minute usage, spending limit / `Stop usage when budget limit is reached`, and whether a payment has failed. A budget cap *can* prevent runner use; the account's actual status is **unknown**. See official [budgets](https://docs.github.com/en/billing/how-tos/set-up-budgets) and [Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions).
3. Open [repository Actions settings](https://github.com/Hailton-Reis/Polaris/settings/actions) to confirm Actions enabled and allowed workflows; review any runner policy.
4. If nothing obvious explains it, try one manual rerun of **one** existing job, not another flurry of commits. Compare `runner_id`, `steps`, exact job banner and any log. Avoid interpreting unchanged zero-step failure as a build compilation result.
5. If runner allocation still fails, submit the IDs, API evidence, timestamps, account/repo settings observations and exact banner message to [GitHub Support](https://support.github.com/). GitHub staff can inspect allocation telemetry unavailable to this connection.

## Minimal GitHub Support description

> In our private repository `Hailton-Reis/Polaris`, two independent Actions workflows fail immediately without executing any steps. Example: run 37825863641, job 113478438938 (2026-10-08). Jobs are created but finish `conclusion=failure`, `steps=[]`, `runner_id=0`, `runner_name=""` within seconds. This happens before checkout, JDK setup, Gradle or Android build. Could you inspect why the hosted runner was not assigned and provide the exact billing/policy/provisioning reason? I will include the exact banner/error and any relevant account-side diagnostics separately.

## Workaround / exit condition

The host-only Kotlin tests can execute locally with JDK21 and Kotlin/coroutines:

```bash
bash scripts/r001/test_spike001_host.sh
python3 -m unittest discover -s scripts/r001 -p 'test_*.py' -v
```

Full APK still requires Android SDK and the clean pinned Yomotsu checkout:

```bash
bash scripts/r001/build_issue002.sh /path/to/pinned-clean-yomotsu /path/to/new-evidence-dir
```

This is **not** equivalent to B01/B02/B03/B04 device acceptance. No Android certification is inferred from successful host tests; do not apply migration 15 before issue #2 is proven in runtime.
