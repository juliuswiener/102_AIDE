import argparse
from pathlib import Path

def cmd_ingest(path: str) -> int:
    p = Path(path)
    if not p.exists():
        print(f"[kb] path not found: {p}")
        return 1
    # TODO: walk and enqueue extraction
    print(f"[kb] ingest stub for: {p}")
    return 0

def cmd_reindex() -> int:
    # TODO: rebuild FTS index
    print("[kb] reindex stub")
    return 0

def cmd_stats() -> int:
    # TODO: print doc/section/tag counts
    print("[kb] stats stub")
    return 0

def main():
    ap = argparse.ArgumentParser(prog="kb")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a_ing = sub.add_parser("ingest")
    a_ing.add_argument("path")
    sub.add_parser("reindex")
    sub.add_parser("stats")
    args = ap.parse_args()
    if args.cmd == "ingest": return raise_on(cmd_ingest(args.path))
    if args.cmd == "reindex": return raise_on(cmd_reindex())
    if args.cmd == "stats": return raise_on(cmd_stats())

def raise_on(code: int):
    import sys
    sys.exit(code)

if __name__ == "__main__":
    main()
