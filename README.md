# AI-Enhanced Attacks on Cloud Infrastructure

*English · [ภาษาไทย](README.th.md)*

A literature review and research proposal on how AI is changing the **speed** and the **identity attack surface** of cloud environments — and a controlled experiment designed to measure one specific consequence of that change.

**Status:** Literature review complete · Presented at UTCC, August 2026 · **Phase 1 first results in** (permission-scope measurement) · behavioral CloudTrail run pending

**Author:** Jarudech Thongkum — Computer Science, University of the Thai Chamber of Commerce

**Slides:** [View presentation on Canva](https://canva.link/xcb7ndjorsurisj)

**Phase 1 lab:** [olafier/iam-blast-radius-lab](https://github.com/olafier/iam-blast-radius-lab)

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

## The experiment

### Research question

> **How does IAM permission scope affect the blast radius of a compromised cloud identity?**

This is deliberately *not* "does least privilege work?" — that question has a known answer and produces no data. This one produces numbers.

### Method

One compromised identity. One **fixed set of actions** spanning read, write, destroy, and escalate. Three IAM policies. Nothing varies except the policy.

The MVP planned 15 actions on S3 + EC2. Phase 1 as run **expanded this to 100 actions across 12 services** (S3, EC2, IAM, STS, Lambda, DynamoDB, KMS, CloudTrail, CloudWatch Logs, Secrets Manager, SSM, RDS), categorised READ 41 · WRITE 26 · DESTROY 20 · ESCALATE 13.

### Two instruments, two kinds of claim

The method distinguishes **what a policy permits** from **what actually happens when an action is attempted**. These need different instruments, and Phase 1 reports only the first.

- **Permission scope — `iam:SimulateCustomPolicy` (done).** Asks AWS whether each action is allowed, with no call executed and nothing created. This is a clean, safe measurement of scope.
- **Behavioral — CloudTrail (pending).** Executes the actions and counts `eventName` + `errorCode` from the log. This is the behavioral experiment the roadmap builds toward; until it is run, the numbers below are permission-level, not behavioral.

```
policy A   eventName TerminateInstances   errorCode AccessDenied   → blocked
policy C   eventName TerminateInstances   errorCode —              → would complete
policy C   eventName CreateRole           errorCode AccessDenied   → blocked (IAM mutation)
```

Without the log there is no behavioral experiment — only a permission measurement. Phase 1 is honest about being the latter.

### Results — permission scope (IAM Policy Simulator, 100 actions)

Full data, chart and the CloudShell run are in [`/lab`](lab) and in [iam-blast-radius-lab](https://github.com/olafier/iam-blast-radius-lab).

| | Policy A — over-permissive | Policy B — moderate | Policy C — least privilege |
|---|---|---|---|
| Actions allowed | **91 / 100** | **43 / 100** | **6 / 100** |
| Action Success Rate | 91.0% | 43.0% | 6.0% |
| Weighted Blast Radius | 83.9% | 25.9% | 3.9% |
| Destructive action possible? | **yes (19/20)** | no (0/20) | no (0/20) |
| Escalation to administrator? | **partial (6/13)** | no (0/13) | no (0/13) |

**The cells the proposal left empty are now filled — at the permission level.** The behavioral CloudTrail pass will re-fill them with executed-and-logged counts.

Two metrics, with weights fixed before the run:

- **ASR** = allowed / total × 100 — every action counts equally.
- **WBR** = Σ weight(allowed) / Σ weight(all) × 100, with READ 1 · WRITE 2 · DESTROY 3 · ESCALATE 4 — actions counted by severity.

Three findings:

1. **Blast radius grows non-linearly with scope.** Least privilege → moderate adds 37 points of ASR but only 22 of WBR (moderate gains READ/WRITE only). Moderate → over-permissive adds 58 points of WBR because DESTROY and ESCALATE open up.
2. **The ASR − WBR gap encodes severity.** The moderate policy succeeds at 43% of actions but 25.9% weighted — it holds nothing destructive. For the over-permissive policy the gap narrows (91 vs 83.9).
3. **"No `iam:*`" ≠ "cannot escalate."** The over-permissive policy is denied all 9 IAM identity-mutation actions, yet still reaches 6 of 13 escalation actions through resource policies and execution paths (`s3:PutBucketPolicy`, `kms:PutKeyPolicy`, `secretsmanager:PutResourcePolicy`, `ec2:AssociateIamInstanceProfile`, `sts:AssumeRole`, `ssm:SendCommand`). This is the mechanism behind UNC6426's "overly permissive" role.

### Scope

**MVP:** IAM policies · fixed action set · permission-scope measurement — **done**

**Next:** CloudTrail behavioral run · OIDC trust · CI/CD identity · automated detection · automated response

---

## Roadmap

| Phase | Focus | State |
|---|---|---|
| **1** | IAM blast-radius — measure permission scope against a fixed action set | **permission-scope done**; behavioral CloudTrail pass pending |
| **2** | OIDC / CI-CD identity — move the setup closer to the real UNC6426 chain | not started |
| **3** | Detection & automated response — can this activity be detected and contained? | not started |
| **Future** | AI-assisted log analysis to speed up investigation | not started |

---

## Repository contents

```
/slides       Presentation deck (PDF)
/notes        Reading notes per source
/sources.md   Every figure mapped to the report it came from
/lab          Phase 1 experiment — IAM policies, action set, runners, results, run evidence
```

The Phase 1 lab is also published standalone at
[olafier/iam-blast-radius-lab](https://github.com/olafier/iam-blast-radius-lab); the copy in
[`/lab`](lab) is kept in sync.

---

## Sources

- [Cloud Security Alliance — Top Threats to Cloud Computing 2026](https://cloudsecurityalliance.org/artifacts/top-threats-cloud-computing-2026)
- [Google Cloud — Cloud Threat Horizons Report H1 2026](https://cloud.google.com/security/report/resources/cloud-threat-horizons-report-h1-2026)
- [Verizon — 2026 Data Breach Investigations Report](https://www.verizon.com/business/resources/reports/dbir/)
- [OWASP GenAI Security Project — Top 10 for LLM Applications 2026](https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/)

---

## A note on honesty

Figures on the slides are traced to a named source. Where a number came through secondary reporting rather than the original report, that is recorded in `sources.md`.

Phase 1 has produced its first results, and this repository is precise about what kind they are: a **permission-scope measurement** from the IAM Policy Simulator, where "allowed" means *permitted by policy*, not *executed and logged*. The **behavioral experiment with CloudTrail as the instrument has not been run yet**, and no simulator figure is presented as a behavioral result. The simulator also sees only identity policies — not SCPs, permission boundaries, target resource policies, or role trust policies.
