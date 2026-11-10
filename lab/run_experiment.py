"""Run the 100-action blast-radius experiment against Policies A/B/C.

  python3 run_experiment.py --mock       # local evaluator, no AWS needed
  python3 run_experiment.py --simulate   # real AWS IAM Policy Simulator (free, creates nothing)

--simulate needs credentials allowed to call iam:SimulateCustomPolicy and sts:GetCallerIdentity.
Output: results/results_raw.json
"""
import argparse
import fnmatch
import json
import os
import sys
from datetime import datetime, timezone

from action_set import ACTIONS, WEIGHTS, resource_arn, service_of

HERE = os.path.dirname(os.path.abspath(__file__))
# Report convention: A = over-permissive, B = moderate, C = least privilege
POLICIES = {
    "A": "policies/policy_A_broad.json",
    "B": "policies/policy_B_moderate.json",
    "C": "policies/policy_C_narrow.json",
}


def load_policy(label):
    with open(os.path.join(HERE, POLICIES[label])) as f:
        return f.read()


# ---------------- mock: simple Allow-statement matcher ----------------
def _as_list(x):
    return x if isinstance(x, list) else [x]


def mock_decision(policy_json, action, resource):
    doc = json.loads(policy_json)
    for st in doc["Statement"]:
        if st.get("Effect") != "Allow":
            continue
        act_ok = any(fnmatch.fnmatchcase(action.lower(), p.lower()) for p in _as_list(st["Action"]))
        res_ok = any(
            p == "*" or fnmatch.fnmatchcase(resource, p) for p in _as_list(st.get("Resource", "*"))
        )
        if act_ok and res_ok:
            return "allowed"
    return "implicitDeny"


def run_mock():
    out = {}
    for label in POLICIES:
        pol = load_policy(label)
        out[label] = {a: mock_decision(pol, a, resource_arn(k)) for a, _, k in ACTIONS}
    return out, {"mode": "mock", "account": "mock", "region": "mock"}


# ---------------- simulate: AWS IAM Policy Simulator ----------------
def run_simulate():
    try:
        import boto3
    except ImportError:
        sys.exit("boto3 not installed: pip install boto3")
    sess = boto3.session.Session()
    region = sess.region_name or "us-east-1"
    account = sess.client("sts").get_caller_identity()["Account"]
    iam = sess.client("iam")

    # group actions by concrete resource ARN (simulator evaluates each action x each resource)
    groups = {}
    for a, _, kind in ACTIONS:
        groups.setdefault(resource_arn(kind, account, region), []).append(a)

    out = {}
    for label in POLICIES:
        pol = load_policy(label)
        decisions = {}
        for arn, actions in groups.items():
            kwargs = {"PolicyInputList": [pol], "ActionNames": actions, "ResourceArns": [arn]}
            while True:
                resp = iam.simulate_custom_policy(**kwargs)
                for r in resp["EvaluationResults"]:
                    decisions[r["EvalActionName"]] = r["EvalDecision"]
                if not resp.get("IsTruncated"):
                    break
                kwargs["Marker"] = resp["Marker"]
        missing = [a for a, _, _ in ACTIONS if a not in decisions]
        if missing:
            sys.exit(f"Policy {label}: simulator returned no result for {missing}")
        out[label] = decisions
        ok = sum(d == "allowed" for d in decisions.values())
        print(f"Policy {label}: {ok}/100 allowed")
    return out, {"mode": "simulate", "account": account[-4:].rjust(12, "*"), "region": region}


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--mock", action="store_true")
    g.add_argument("--simulate", action="store_true")
    args = ap.parse_args()

    decisions, meta = run_mock() if args.mock else run_simulate()
    rows = []
    for a, cat, kind in ACTIONS:
        row = {"action": a, "service": service_of(a), "category": cat, "weight": WEIGHTS[cat]}
        for label in POLICIES:
            row[f"policy_{label}"] = decisions[label][a]
        rows.append(row)

    meta["timestamp"] = datetime.now(timezone.utc).isoformat()
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    path = os.path.join(HERE, "results", "results_raw.json")
    with open(path, "w") as f:
        json.dump({"meta": meta, "results": rows}, f, indent=2)
    print(f"wrote {path} ({meta['mode']})")


if __name__ == "__main__":
    main()
