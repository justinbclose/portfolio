# Portfolio Visitors tracker (source)

This branch holds the page for Justin's private **Portfolio Visitors** tracker
(a claude.ai artifact). It is kept off `main` on purpose, so GitHub Pages never
serves it on justinbclose.com.

- `index.html` — the tracker page. `map-us.json`, `map-world.json` — map shapes.
- **This branch is the source of truth.** The "Portfolio dashboard sync" scheduled
  task runs every 2 hours: it pulls fresh GA4 numbers (from the `stats` branch)
  and, if any file here differs from the live tracker, republishes the tracker
  from this branch. Push here and the tracker updates within 2 hours.
- No visitor data or company names live here. Stats come from the tracker's own
  private data store (`stats/latest`), and company display names from `meta/names`.
