#!/usr/bin/env python3
"""
dedup.py — find duplicates across a NAS media library, by TMDB id only.

Runs LOCALLY on the NAS (e.g. as a Synology Task Scheduler job). It scans one
or more directories and reports every TMDB id that appears more than once —
nothing else is compared, only the [tmdbid-XXXXX] tag embedded in names.

What carries an id (and is therefore counted):
  * video files whose name contains [tmdbid-XXXXX]   (movie libraries),
  * folders whose name contains [tmdbid-XXXXX]        (series libraries).
A TMDB id found on two or more such entries is reported as a duplicate group.

The program only READS the filesystem — it never renames, moves or deletes
anything. The result is written to a log file and printed to the console.

Usage:
  python3 dedup.py /volume1/video/Movies
  python3 dedup.py /volume1/video/Movies "/volume1/video/TV/Series"
  python3 dedup.py --log /volume1/logs/dedup.log /volume1/video/Movies
"""

import argparse
import logging
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

VIDEO_EXT = {'.ts', '.mkv', '.mp4', '.avi', '.m4v', '.mov', '.wmv', '.mpg', '.mpeg', '.m2ts'}
RE_TMDBID = re.compile(r'\[tmdbid-(\d+)\]', re.IGNORECASE)

log = logging.getLogger('dedup')


def setup_logging(log_path):
    log.setLevel(logging.INFO)
    log.handlers.clear()
    fmt = logging.Formatter('%(asctime)s  %(levelname)s  %(message)s', '%Y-%m-%d %H:%M:%S')
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    log.addHandler(ch)
    if log_path:
        try:
            fh = logging.FileHandler(log_path, encoding='utf-8')
            fh.setFormatter(fmt)
            log.addHandler(fh)
        except OSError as exc:
            log.warning('Could not open log file (%s): %s', log_path, exc)


def scan(path, by_id):
    """Add every id-tagged folder and video file under `path` to the by_id map
    ({tmdbid: set(paths)}). Returns the number of tagged entries found."""
    found = 0
    for dirpath, dirnames, filenames in os.walk(path):
        dirnames[:] = [d for d in dirnames if d != '@eaDir']
        for d in dirnames:
            m = RE_TMDBID.search(d)
            if m:
                by_id.setdefault(int(m.group(1)), set()).add(
                    os.path.realpath(os.path.join(dirpath, d)))
                found += 1
        for f in filenames:
            if os.path.splitext(f)[1].lower() not in VIDEO_EXT:
                continue
            m = RE_TMDBID.search(f)
            if m:
                by_id.setdefault(int(m.group(1)), set()).add(
                    os.path.realpath(os.path.join(dirpath, f)))
                found += 1
    return found


def main():
    ap = argparse.ArgumentParser(
        description='Find duplicates in a NAS media library by TMDB id (read-only).')
    ap.add_argument('paths', nargs='*', help='one or more directories to scan')
    ap.add_argument('--log', default=None, help='log file path (default: dedup.log next to the script)')
    ap.add_argument('--no-log', action='store_true', help='do not write a log file')
    args = ap.parse_args()

    log_path = None if args.no_log else (args.log or os.path.join(SCRIPT_DIR, 'dedup.log'))
    setup_logging(log_path)

    if not args.paths:
        log.error('No paths given. Usage: python3 dedup.py /path/one ["/path/two" ...]')
        sys.exit(1)

    # Keep only existing directories; drop duplicates / nested repeats by realpath.
    seen, roots = set(), []
    for p in args.paths:
        rp = os.path.realpath(p.rstrip('/'))
        if not os.path.isdir(rp):
            log.error('Not a directory, skipping: %s', p)
            continue
        if rp not in seen:
            seen.add(rp)
            roots.append(rp)
    if not roots:
        log.error('None of the given paths is a directory.')
        sys.exit(1)

    log.info('==== START ==== scanning %d path(s)', len(roots))

    by_id = {}
    total = 0
    for root in roots:
        n = scan(root, by_id)
        total += n
        log.info('Scanned: %s  (%d tagged entries)', root, n)

    dups = {tid: sorted(paths) for tid, paths in by_id.items() if len(paths) > 1}

    log.info('Distinct TMDB ids: %d | tagged entries: %d | DUPLICATE ids: %d',
             len(by_id), total, len(dups))

    dup_entries = 0
    for tid in sorted(dups):
        paths = dups[tid]
        dup_entries += len(paths)
        log.info('tmdbid-%d (%d copies):', tid, len(paths))
        for p in paths:
            log.info('    %s', p)

    log.info('==== DONE ====')
    if dups:
        log.info('Found %d duplicate id(s) across %d entries.', len(dups), dup_entries)
    else:
        log.info('No duplicates found.')


if __name__ == '__main__':
    main()
