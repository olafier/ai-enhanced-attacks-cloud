"""measure_principal.py — run in CloudShell (as the researcher, not as the role).

Measures the EFFECTIVE permissions of the deployed roles blast-lab-role-A/B/C using
iam:SimulatePrincipalPolicy against the real role ARNs. Unlike SimulateCustomPolicy
(which judges a policy document in isolation), this evaluates the role as actually
deployed, including any permissions boundary or attached managed policies.

Writes results/results_principal.json and prints a comparison against
results/results_raw.json (the custom-policy simulation) if present.
"""
import json
import os
import sys

from action_set import ACTIONS, WEIGHTS, resource_arn, service_of

try:
    import boto3
except ImportError:
    sys.exit("boto3 not installed: pip3 install boto3")

HERE = os.path.dirname(os.path.abspath(__file__))
ROLES = {"A": "blast-lab-role-A", "B": "blast-lab-role-B", "C": "blast-lab-role-C"}


def main():
    sess = boto3.session.Session()
    region = sess.region_name or "ap-southeast-1"
    account = sess.client("sts").get_caller_identity()["Account"]
    iam = sess.client("iam")

    groups = {}
    for a, _, kind in ACTIONS:
        groups.setdefault(resource_arn(kind, account, region), []).append(a)

    out = {}
    for label, role in ROLES.items():
        role_arn = f"arn:aws:iam::{account}:role/{role}"
        decisions = {}
        for arn, actions in groups.items():
            kwargs = {"PolicySourceArn": role_arn, "ActionNames": actions,
                      "ResourceArns": [arn]}
            while True:
                resp = iam.simulate_principal_policy(**kwargs)
                for r in resp["EvaluationResults"]:
                    decisions[r["EvalActionName"]] = r["EvalDecision"]
                if not resp.get("IsTruncated"):
                    break
                kwargs["Marker"] = resp["Marker"]
        out[label] = decisions
        ok = sum(d == "allowed" for d in decisions.values())
        print(f"Role {label} ({role}): {ok}/100 allowed")

    rows = []
    for a, cat, kind in ACTIONS:
        row = {"action": a, "service": service_of(a), "category": cat, "weight": WEIGHTS[cat]}
        for label in ROLES:
            row[f"role_{label}"] = out[label][a]
        rows.append(row)
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    with open(os.path.join(HERE, "results", "results_principal.json"), "w") as f:
        json.dump({"meta": {"mode": "simulate_principal", "account": account[-4:].rjust(12, "*"),
                            "region": region}, "results": rows}, f, indent=2)
    print("wrote results/results_principal.json")

    # compare to custom-policy simulation if available
    raw_path = os.path.join(HERE, "results", "results_raw.json")
    if not os.path.exists(raw_path):
        print("\n(no results_raw.json to compare — run run_experiment.py --simulate first)")
        return
    raw = {r["action"]: r for r in json.load(open(raw_path))["results"]}
    print("\nEffective (role) vs policy-document simulation:")
    any_diff = False
    for label in ROLES:
        diffs = []
        for a, _, _ in ACTIONS:
            eff = out[label][a]
            base = raw[a].get(f"policy_{label}")
            if (eff == "allowed") != (base == "allowed"):
                diffs.append(f"{a}: policy={base} effective={eff}")
        if diffs:
            any_diff = True
            print(f"  Role {label}: {len(diffs)} differences")
            for d in diffs:
                print(f"    {d}")
        else:
            print(f"  Role {label}: identical (no boundary narrowed the role)")
    if not any_diff:
        print("\nFinding: deployed roles grant exactly what the policy documents imply;"
              " no permissions boundary or managed policy changed the effective scope.")


if __name__ == "__main__":
    main()
