# jduplicates

Scan one or more NAS libraries and report duplicates — **by TMDB id only**.
Read-only: it never renames, moves or deletes anything. Companion to jmovies/jseries.

A `[tmdbid-XXXXX]` tag found on two or more video files or folders is reported
as a duplicate group (works across all scanned paths together).

## Use

```
python3 organize.py --dir "/volume1/video/Movies" --dir "/volume1/video/Series"
```

- `--dir` can be repeated; paths may also be listed as `path=` lines in `config.txt`.
- No TMDB key needed — it only reads names.
- Result goes to a dated log next to the script: `jduplicates-YYYY-MM-DD.log`.

Requires Python 3.
