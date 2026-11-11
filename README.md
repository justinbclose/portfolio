# Justin Close — Marketing Portfolio

Source for my portfolio website, hosted on GitHub Pages.

- `index.html` — the whole site. Projects live in the `WORK` list near the bottom.
- `img/` — photos and work samples.

## Analytics
- GA4 tag + custom events live in the last `<script>` of `index.html`. Set `GA_ID` there.
- Short links: `?ref=li`, `?ref=resume`, `?ref=sig`, `?ref=canva`, `?ref=app-<company>` become UTM tags in GA4.
- `?me=1` stops counting your own visits in that browser; `?me=0` undoes it.
- `.github/workflows/stats.yml` pulls GA4 every 2 hours and saves an encrypted `stats.enc.json` to the `stats` branch (signs in keyless via `analytics/gcp.sh`; one secret: `DASH_KEY`).
