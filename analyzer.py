#!/usr/bin/env python
"""CLI:  python analyzer.py deployment.log  [--json] [--no-llm] [--no-ml] [--report out.md] [--trace]"""
import argparse, json, sys
from troubleshooter.agent import TroubleshootingAgent
from troubleshooter.feedback import save_analysis
from troubleshooter.report import to_markdown


def main():
    ap = argparse.ArgumentParser(description="AI Deployment Issue Troubleshooting Assistant")
    ap.add_argument("logfile", help="path to log file, or - for stdin")
    ap.add_argument("--json", action="store_true"); ap.add_argument("--no-llm", action="store_true")
    ap.add_argument("--no-ml", action="store_true"); ap.add_argument("--report"); ap.add_argument("--trace", action="store_true")
    a = ap.parse_args()
    text = sys.stdin.read() if a.logfile == "-" else open(a.logfile, encoding="utf-8", errors="replace").read()
    r = TroubleshootingAgent(use_llm=not a.no_llm, use_ml=not a.no_ml).analyze(text)
    try: save_analysis(r)
    except Exception: pass
    if a.json:
        print(json.dumps(r.to_dict(), indent=2)); return
    print(f"Issue Type: {r.issue_type}\nSeverity: {r.severity}\nRoot Cause: {r.root_cause}\nRecommendation: {r.quick_fix or r.recommended_actions[0]}")
    print(f"Confidence: {r.confidence:.0%}" + ("  [NEEDS HUMAN REVIEW]" if r.needs_human_review else "") + f"   Engine: {r.mode}   ({r.latency_s}s)")
    print(f"\nSummary:\n  {r.summary}\n\nRecommended actions:")
    for i, s in enumerate(r.recommended_actions, 1): print(f"  {i}. {s}")
    print("\nValidation:"); [print(f"  - {s}") for s in r.validation_steps]
    if a.trace:
        print("\nAgent trace:"); [print(f"  {s['step']:<22} {s['detail']}  ({s['ms']} ms)") for s in r.trace]
    if a.report:
        open(a.report, "w", encoding="utf-8").write(to_markdown(r)); print(f"\nReport written to {a.report}")


if __name__ == "__main__":
    main()
