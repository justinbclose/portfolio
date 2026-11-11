# UX Spec: Justin Close Portfolio, "Contour Gallery"

## 1. Direction
**Contour Gallery.** We keep the template structure: hero, caps name with a gold period, 01/02/03 chapters, center timeline, contact panel. The hard rectangles are replaced with topographic contour lines from Justin's drone and mountain world. The work hangs like a gallery show: each piece shown whole on a soft mat, with a museum wall label.

Aman's luxury comes from full-bleed photos and tiny tracked caps, but its edges are sharp. Contours keep that restraint and add flow from Justin's world, with no AI tells (terracotta, centered layouts, card grids, Inter).

## 2. Tokens (single light theme with deep-sage sections)
**On cream:**
- `--cream` #f5f5ef (page)
- `--mat` #ecebdf (exhibit mats, inputs)
- `--mat-2` #e2e1d0 (hover, chips)
- `--ink` #23261c (text)
- `--muted` #5c604f (6:1 on cream)
- `--line` #d3d1bd (hairlines)
- `--sage` #8d9765 (fills only)
- `--sage-ink` #4e5636 (sage text and links)
- `--gold-ink` #8a6636 (gold text on cream)

**Deep sections:**
- `--deep` #2f3524
- `--deep-2` #3b4230
- `--on-deep` #f5f5ef
- `--on-deep-muted` #c7c9b3

**Accent:**
- `--gold` #d3a877 (the period, rings, contours)
- `--on-accent` #23261c

**Shape:** radii `--r-mat` 28px, `--r-sm` 14px, pill 999px.
**Spacing:** 4/8/12/16/24/32/48/72/112/160.
**Shadow:** one only, `--lift: 0 24px 60px -28px rgba(35,38,28,.35)`.

## 3. Type (Google Fonts)
- **Italiana** (display): uppercase, tracking .08em. It has the look of an inscribed hotel facade sign.
- **Hanken Grotesk** 400/500/600: body.
- **Azeret Mono** 500: numerals, stats, caption keys, dates.

**Scale:**
- H1: clamp(54px, 11vw, 148px)/.95
- H2: clamp(40px, 6vw, 84px)/1
- H3: Hanken 600, 22px/1.25
- Lead: clamp(19px, 2vw, 23px)/1.5
- Body: 17px/1.65
- Label: Azeret 11.5px, .22em, caps
- Stat: Azeret clamp(44px, 7vw, 72px)

The gold period is a `<span class="dot">`: a 0.16em gold circle on the baseline.

## 4. Removing the blockiness
- **Contour dividers** between sections: an inline SVG (viewBox 1440×120, `preserveAspectRatio="none"`, height clamp(60px, 9vw, 120px)). It holds one filled wave in the next section's colour plus 3 gold 1px hairlines tracing it 8px apart (opacity .55/.35/.2). Use a unique path for each divider.
- **Hero** photo ends in a wave mask, not a straight edge. The **portrait** is a summit arch (`border-radius: 999px 999px 28px 28px`). The contact aerial gets a wave top.
- **Overlap:** About text overlaps the portrait by 48px; giant `--line` numerals sit behind the H2s.
- **Layout:** asymmetric 7/12 + 5/12 grids. Only the hero name is centered.
- **Space:** 112–160px between sections (72px on phone).
- **No boxes** around skills or jobs: use hairlines and air.

## 5. Button: "Trail Marker"
The pill:
- 54px tall, padding `0 26px 0 6px`, radius 999px.
- 1.5px `currentColor` border, `overflow: hidden`.
- Label in Azeret 12px, .18em tracking.

The marker:
- `::before` is a 42px gold circle in the left end, holding an SVG arrow in `--on-accent`.

**Hover/focus (fine pointer):**
- The circle grows to flood the pill: `transform: scale(var(--fill))`, with `--fill` set by JS from width ÷ 42, origin `27px 50%`, 520ms.
- The label cross-fades to `--on-accent` through stacked spans.
- The arrow slides 6px right.

**Other states:**
- **Active:** scale .97.
- **`:focus-visible`:** 2px outline, offset 4px. `--gold` on deep, `--gold-ink` on cream.
- **Touch:** the marker pulses once (1→1.12→1, 400ms).

**Copy buttons:** a 36px circle in a 44px hit area, with an `aria-label`.

## 6. Portfolio: the Exhibit
- **Filter chips** sit in a sticky rail: 40px pills in `--mat`. The active chip gets `--sage-ink` text and a gold dot.
- **Each piece** is an `<article class="exhibit">`:
  - The mat is `--mat` with `--r-mat` radius and `--lift`, padding clamp(14px, 3vw, 32px).
  - The image is `width: 100%; height: auto`, with 4px radius and a 1px `--line` hairline.
  - **Never `object-fit: cover`, never a fixed aspect box.**
  - **Desktop only:** pieces cap at `max-height: 86svh; width: auto`, centered, so the whole page shows. Phones use natural height, so the eblast is a long readable column.
- **Wall label:** a `<dl>` under a 24px gold contour tick. Keys are Azeret `--muted`, values Hanken. The keys are CLIENT, PIECE, RAN IN / SENT TO / PUBLISHED ON, ROLE, RESULT. Add data fields `ranLabel`, `ranIn`, `role`, `result`.
- **Seed values:**

| Piece | Label | Value |
|---|---|---|
| Marine ad | Ran in | San Diego Magazine |
| LJBTC ad | Ran in | Modern Luxury |
| Shores eblast | Sent to | 84,000 subscribers |
| W2W email | Sent via | Shopify Email |
| Wedding LP | Published on | ljbtc.com |
| Marine copy | Published on | marineroom.com |
| Mash | | Instagram & Facebook |
| Tourmaline | | Google Business Profile & print |
| Utah Tech | | To confirm with Justin. Don't invent outlets. |

- **"What I did"** becomes a `<details>` ("How I made it +") under the label.
- **Phone layout:** one column (mat, label, then a 48px gap).
- **Desktop "salon hang"** on 12 columns. JS reads `naturalWidth / naturalHeight` and sets a class:
  - `.wide` (>1.45): 12 columns, label split into two columns below.
  - `.portrait`/`.tall`: 6–7 columns with the label beside it. Sides alternate, and every second one is offset `translateY(80px)`.
  - `.square`: 5 columns.
- **Multi-image pieces** stack in one mat (12px gaps).
- **Marine strip:** also set its copy as a live pull quote.
- **social-ljbtc.jpg** is a wide exhibit. It already has phone frames, so don't double-frame it.

## 7. CSS phone mockup (`.phone`)
- **Body:** `width: clamp(220px, 62vw, 300px); aspect-ratio: 9/19.5`, radius `15%/7%`, background #1c1d18, padding 3.2%.
  - Titanium edge: `box-shadow: inset 0 0 0 1.5px #5a5c52, inset 0 0 0 4px #121310`, plus `--lift`.
- **Screen:** radius `12%/5.6%`, `overflow: hidden`, black background.
  - Dynamic Island: `::before`, 31% × 3.4%, pill, top 2.2%, centered.
- **Side buttons:** spans in #3d3f36, 3px wide, 2px radius, 2px outside the body.
  - Left: action (top 17%, 5% tall) and two volume buttons (25% and 36%, 9% tall).
  - Right: power (29%, 13% tall).
- **Auto-scroll:** the `<img>` is `width: 100%; height: auto`. If it's taller than the screen, run a keyframe from `translateY(0)` to `-(imgH − screenH)`.
  - Timing: 9s ease-in-out, alternate, with 1.5s holds at each end.
  - Starts in view only (IntersectionObserver).
  - Pauses on hover, pointerdown and focus.
- **Reels** (reel-1..8, 9:16) center on the black screen with a CSS Reels overlay: @justinbretclose, a heart/comment/share column, and a caption line.
  - Rail: scroll-snap. The centered phone is at scale 1; neighbours at .9 and opacity .7.
- **mash-ig / mash-fb:** two phones side by side in one mat, stacked on phones.
- **Reduced motion:** no auto-scroll or scaling; screens use native `overflow-y: auto`.

## 8. Timeline
- **Trail:** a meandering SVG trail down a deep-sage section, at 24px from the left on phones. It's 1.5px gold at .6 opacity, drawn in with `stroke-dashoffset` tied to scroll in one rAF loop.
- **Nodes:** 14px gold rings. The current role is filled, with a 3s halo pulse.
- **Entries** alternate sides on desktop, with no boxes.

## 9. Motion
- **Easing:** `--ease: cubic-bezier(.22, .8, .24, 1)`.
- **Durations:** 200ms UI, 520ms buttons, 900ms reveals.
- **Properties:** transform and opacity only. The timeline stroke is the one exception.
- **Reveals:** exhibits rise 28px and fade in once, staggered 80ms.
- **Reduced motion:** `prefers-reduced-motion` turns all of it off.

## 10. Do's and don'ts
**Do:**
- Show every piece whole and label every outlet.
- Keep taps ≥ 44px and text contrast ≥ 4.5:1.
- Give every image `loading="lazy"` plus width/height.
- Ship one HTML file with vanilla JS.

**Don't:**
- Use `object-fit: cover` on work, square card grids, or zero-radius rectangles.
- Add a second shadow.
- Put gold text on cream.
- Hide content behind clicks.
- Use emoji.

## 11. Signature moment: "The Drop"
1. After the name rises, the gold period lands with an 8px bounce.
2. Three slightly irregular gold contour rings ripple out from it across the hero, like a stone dropped into the turquoise water in his drone shot.
   - Motion: scale 0→6, opacity .7→0, 2.4s, staggered 300ms.
   - Once per visit (sessionStorage).
3. The same gold hairlines return in every divider and the timeline, so the page reads as rings spreading from one dot.
