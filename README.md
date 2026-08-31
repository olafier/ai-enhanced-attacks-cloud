# AI-Enhanced Attacks on Cloud Infrastructure

*English · [ภาษาไทย](README.th.md)*

A literature review and research proposal on how AI is changing the **speed** and the **identity attack surface** of cloud environments — and a controlled experiment designed to measure one specific consequence of that change.

**Status:** Literature review complete · Presented at UTCC, August 2026 · Experiment not yet run

**Author:** Jarudech Thongkum — Computer Science, University of the Thai Chamber of Commerce

---

## The problem

Across four independent 2026 industry reports, the same shift appears: attackers are not inventing new techniques. They are executing existing ones faster, and the thing they attack most reliably is **identity**.

| Source | What it reports |
|---|---|
| CSA — Top Threats to Cloud Computing 2026 | *AI-Enhanced Attacks* enters at **#2**; *Inadequate IAM* is **#1**; misconfiguration falls from #1 to #5 |
| Google Cloud — Threat Horizons H1 2026 | Software vulnerability exploitation rises from **2.9% → 44.5%** of initial access; third-party compromise involved in **21%** of cases |
| Verizon — DBIR 2026 | Vulnerability exploitation overtakes credential theft as the top breach vector (**≈31%**); third-party involvement at **48%**, up **60%** year over year |
| OWASP — GenAI Top 10 2026 | *Excessive Agency* rises in the rankings — AI systems given more permission than the task requires |

Two datasets collected on completely different populations point the same direction. That agreement is the finding.

---

## The case study — UNC6426

Google Cloud documents a single intrusion that compresses the whole argument into **under 72 hours**. Every step below is quoted or paraphrased directly from the report.

```
Day 1   Compromised Nx npm package → developer installs update → malicious code runs
        QUIETVAULT harvests GitHub + NPM API keys
        ↳ "using AI that assisted with identifying files of interest"   ← the only AI step
        Keys uploaded to a public GitHub repository

Day 3   Attacker uses stolen keys to enter GitHub, enumerates the environment
        Abuses the GitHub-to-AWS OIDC trust relationship
        ↳ generates temporary AWS STS tokens for the Github-Actions-CloudFormation role

Day 4   "The compromised Github-Actions-CloudFormation role was overly permissive."
        Deploys a CloudFormation stack whose sole purpose is to create an IAM role
        with AdministratorAccess attached
        Exfiltrates S3 objects, terminates production EC2 and RDS instances,
        decrypts application keys
```

**No zero-day. No novel technique.** AI performed one step in the middle — the part a human used to do by hand.

The sentence that matters most for what comes next is the one Google wrote plainly: *the role was overly permissive.*

---

## The proposed experiment

### Research question

> **How does IAM permission scope affect the blast radius of a compromised cloud identity?**

This is deliberately *not* "does least privilege work?" — that question has a known answer and produces no data. This one produces numbers.

### Method

One compromised identity. One fixed set of **15 actions** spanning read, write, destroy, and escalate. Three IAM policies. Nothing varies except the policy.

| | Policy A | Policy B | Policy C |
|---|---|---|---|
| | over-permissive | moderate | least privilege |
| Actions the identity completed | ? / 15 | ? / 15 | ? / 15 |
| Distinct resources reached | ? | ? | ? |
| Destructive action possible? | yes / no | yes / no | yes / no |
| Escalation to administrator? | yes / no | yes / no | yes / no |

**The cells are empty on purpose.** Filling them is the work.

### Why CloudTrail is the instrument, not decoration

Every API call is logged with `eventName` and `errorCode`. Counting those log lines is what converts *"what could the attacker do"* from an opinion into a measurement.

```
policy A   eventName TerminateInstances   errorCode —              → counted as completed
policy B   eventName TerminateInstances   errorCode AccessDenied   → counted as blocked
policy C   eventName CreateRole           errorCode AccessDenied   → counted as blocked
```

Without the log there is no experiment — only a demonstration.

### Scope

**MVP:** IAM policies · S3 + EC2 · fixed action set · CloudTrail measurement

**Later:** OIDC trust · CI/CD identity · automated detection · automated response

---

## Roadmap

| Phase | Focus |
|---|---|
| **1** | IAM blast-radius experiment — measure permission scope against a fixed action set |
| **2** | OIDC / CI-CD identity — move the setup closer to the real UNC6426 chain |
| **3** | Detection & automated response — can this activity be detected and contained? |
| **Future** | AI-assisted log analysis to speed up investigation |

---

## Repository contents

```
/slides       Presentation deck (PDF)
/notes        Reading notes per source
/sources.md   Every figure mapped to the report it came from
/lab          IAM policies and action scripts  (Phase 1 — in progress)
```

---

## Sources

- [Cloud Security Alliance — Top Threats to Cloud Computing 2026](https://cloudsecurityalliance.org/artifacts/top-threats-cloud-computing-2026)
- [Google Cloud — Cloud Threat Horizons Report H1 2026](https://cloud.google.com/security/report/resources/cloud-threat-horizons-report-h1-2026)
- [Verizon — 2026 Data Breach Investigations Report](https://www.verizon.com/business/resources/reports/dbir/)
- [OWASP GenAI Security Project — Top 10 for LLM Applications 2026](https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/)

---

## A note on honesty

Figures on the slides are traced to a named source. Where a number came through secondary reporting rather than the original report, that is recorded in `sources.md`. The experiment described above **has not been run** — nothing in this repository presents expected results as collected data.
