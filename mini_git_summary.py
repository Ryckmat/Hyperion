#!/usr/bin/env python3
import subprocess, collections, json, datetime as dt

def sh(*args):
    out = subprocess.check_output(args, stderr=subprocess.DEVNULL)
    return out.decode("utf-8", "ignore").splitlines()

# Commits
tsv = sh("git","log","--date=iso","--pretty=format:%H|%an <%ae>|%ad|%s")
commits = len(tsv)
authors = set()
dates = []
for l in tsv:
    parts = l.split("|", 3)
    if len(parts) >= 3:
        authors.add(parts[1])
        try:
            dates.append(dt.datetime.fromisoformat(parts[2].replace("Z","+00:00")))
        except Exception:
            pass
first = min(dates).strftime("%Y-%m-%d %H:%M:%S %z") if dates else None
last  = max(dates).strftime("%Y-%m-%d %H:%M:%S %z") if dates else None

# Hotspots
num = sh("git","log","--numstat","--pretty=format:")
changes = collections.Counter()
for line in num:
    parts = line.split("\t")
    if len(parts) == 3:
        add, rem, path = parts
        try:
            a = 0 if add == "-" else int(add)
            r = 0 if rem == "-" else int(rem)
        except ValueError:
            a, r = 0, 0
        changes[path] += a + r

hotspots = [{"path": p, "changes": c} for p, c in changes.most_common(10)]

summary = {
    "commits": commits,
    "first_commit": first,
    "last_commit": last,
    "contributors": len(authors),
    "hotspots_top10": hotspots
}
print(json.dumps(summary, ensure_ascii=False, indent=2))
