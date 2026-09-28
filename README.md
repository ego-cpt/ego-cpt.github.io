# EgoCPT project website

Static research project page based on the **original NeRFies template**:
<https://nerfies.github.io/>. No framework, package installation, tracking,
external JavaScript, or build service is required to view it.

## Content

- Title and abstract: the author's approved final text.
- The Paper button says "coming soon" and is disabled. The manuscript remains
  withheld during double-blind review; no PDF or manuscript link is included.
- Authors, in the user-confirmed order: Zhixin Sun*, Kairui Shi, Tianao Ren,
  Ming Yang, Mark Cutkosky, James Jingxi Xu.
- Each author name links to the user's supplied personal homepage or profile,
  opening in a new tab; affiliation superscripts remain outside the link.
- Tianao Ren and Mark Cutkosky: Stanford University. All other authors:
  Ant Group. No affiliations inferred from another project's website.
- Header logos: the exact Ant Group and Stanford PNGs used by
  <https://ume-exo.github.io/>, as requested. Original artwork and colors are
  unchanged; local copies work without third-party image requests. Hashes and
  sources are recorded in `static/logos/provenance.json` and checked on deploy.
- The star after Zhixin Sun is retained exactly as supplied. Its meaning has
  not been supplied; the page does not invent an equal-contribution or
  corresponding-author note.
- Latest approved light supplementary video (cut 16), three real
  robot clips, method figure, contact comparisons, EgoDex/TACO examples.
- Hardware clips use the approved continuous 1x windows: pouring [1,11)s,
  lint rolling [4,10)s, sweeping [12.5,18.5)s. No trials are spliced.
- The stapler example keeps frames 0–89 at 30 fps (3 seconds), before hand
  release. At the author's request, its opening object transform is held at
  frame 36 (1.2 seconds, grasp onset) until that frame. This covers the requested
  first 1.1 seconds without a jump at the handoff. Hand motion, later object
  motion, camera, materials, playback speed and native 1080p resolution are
  unchanged. The author requested removal of the hold/release explanation from
  the visible caption; this local documentation retains the edit provenance.
  The original reference, original video and Before/After comparison remain
  preserved.
- Eleven contact sliders cover five EgoDex tasks and five TACO tasks.
  The original cup-penetration and bottle-grasp examples lead the section,
  followed by four EgoDex details and a separate group of five TACO comparisons.
  TACO now includes rolling and surface brushing in addition to
  the original pouring, bowl/ladle and container examples.
  Each new detail isolates one complete hand
  and its object, with the same frame, camera, materials, and lighting in both
  states. Blue and pink identify left and right hands, not methods.
  "Before" in the task details is the saved input to episode contact optimization,
  not a claim that every input was produced by the same vanilla baseline.
- All non-hardware video sources are 1920×1080. The supplementary film uses its
  native 1080p master; gallery videos are rendered again from archived geometry
  and poses. No solver or physics rollout is rerun for the website.
- The three D455 originals in the project-root `videos.zip` are 1280×720 at
  30 fps and byte-identical to the recordings used for the existing real-robot
  clips. Those approved clips and crops are preserved without upscaling.
- The local Apple Design skill informs direct pointer tracking, grab-offset
  preservation, touch and keyboard access, 44 px handles, and motion preferences.
- Hardware replay with right-hand glove control and reconstructed-reference
  visualization are labeled separately; the page does not relabel either as
  new autonomous policy evaluation.

## Preview

On 2026-09-28 the author explicitly approved publication of the current
reviewed version, superseding the earlier private-preview-only restriction.
The Paper button remains "coming soon"; the manuscript is not part of this
release. The local preview remains available for subsequent edits.

From this directory:

```bash
node scripts/verify_site.mjs
node scripts/serve.mjs
```

Open <http://localhost:8765/> (forward port 8765 in VS Code when using SSH).
The server binds only to `127.0.0.1`, not a LAN/public interface. Use a private
SSH/VS Code port forward; do not create a public tunnel. The manuscript,
`_local/`, `.git/`, and source scripts are not served.
`index.html` also opens directly; clipboard support depends on the browser.
The preview server supports HTTP byte ranges for seeking within MP4s. It serves
only public files, not `.git`, source scripts, or `_local` browser profiles.

Optional Chrome-based checks and screenshots:

```bash
node scripts/check_browser.mjs
```

These use a fresh headless browser profile, not your signed-in browser. Results
are kept under `_local/` and excluded from Git and Pages.

## Deploy to GitHub Pages

The approved release targets the existing `Applewonder/EgoCPT.github.io`
repository and its **project-site** URL:

<https://applewonder.github.io/EgoCPT.github.io/>

The canonical and social-sharing URLs point to this project site, not to
`egocpt.github.io`. No custom domain or CNAME is configured.

1. Keep the paper PDF out of the public tree and deployment artifacts; the
   original local manuscript is preserved. The approved website release does
   not change the "coming soon" Paper button.
2. In the repository's **Settings → Pages**, set **Source → GitHub Actions**.
3. Commit these website files and push `main`. The included Pages workflow
   validates local assets, packages only `index.html`, `sitemap.xml`, the exact
   Google ownership-verification file, `static/`, `.nojekyll`, and
   `THIRD_PARTY.md`, then deploys the site.
4. Inspect the completed **Deploy project website** action and its actual URL.

The one-time Pages setting in step 2 requires repository administration
access. A successful `git push` alone does not enable Pages. If the build
fails at `actions/configure-pages` and the repository still reports
`has_pages: false`, enable **GitHub Actions** at
<https://github.com/Applewonder/EgoCPT.github.io/settings/pages>, then rerun
the latest workflow at
<https://github.com/Applewonder/EgoCPT.github.io/actions>.
Do not treat an uploaded commit or a failed workflow as a live website.

No push, repository visibility change, or public deployment is performed by
the preparation scripts. The website uses relative paths so it works at either
a project URL or a root domain. The public code and arXiv links remain unset;
Paper and Code explicitly say "coming soon".

Official deployment documentation:
<https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages>

## Search indexing

The canonical URL is `https://applewonder.github.io/EgoCPT.github.io/`.
`sitemap.xml` lists that single page; section fragments and duplicate
`index.html` URLs are not separate sitemap entries. Publishing the site or
sitemap does not itself submit an indexing request or guarantee search results.

To request Google indexing, the owner can add this exact URL as a **URL-prefix**
property in [Search Console](https://search.google.com/search-console/welcome).
The author supplied **HTML file** verification on 2026-09-28:
`googlefc25602e21eda673.html` contains the exact Google-provided verification
line and is published at the project root. Click **Verify** in the owner's
Search Console once that file is live. Keep the file available for future
ownership checks. If the property is already verified, reuse it.
Then submit `sitemap.xml` under **Sitemaps** and inspect the canonical URL using
**URL inspection → Request indexing**. This requires the owner's Google account;
publishing through GitHub does not provide Search Console access.

Google can take days to weeks to crawl a new or updated page, and a request
does not guarantee inclusion. See [Google's recrawl guidance](https://developers.google.com/search/docs/crawling-indexing/ask-google-to-recrawl)
and [ownership verification instructions](https://support.google.com/webmasters/answer/9008080).
For this project site, Google checks `https://applewonder.github.io/robots.txt`,
not a file under `/EgoCPT.github.io/`. The host-level robots file returned 404
during the 2026-09-28 audit, which Google treats as no crawl restrictions; no
ineffective subdirectory robots file is added.

## Edit and regenerate

- `index.html`: title, authors, affiliations, abstract, captions, links, BibTeX.
- `static/css/site.css`: responsive overrides on the original Bulma/NeRFies CSS.
- `static/js/site.js`: comparison sliders, view-aware video playback, citation copy.
- `scripts/prepare_assets.mjs`: optional, local-workspace media preparation;
  requires Node, FFmpeg, and the original project files. Do not run it on an
  already populated asset directory: derived files are not overwritten.
- `_local/asset_manifest.json`: local-only SHA-256, sizes, exact sources and trims.
  It is ignored by Git and excluded from the deployment artifact.
- `scripts/prepare_hd_comparisons.py`: verifies the archived scenes and rebuilds
  the saved input hand poses with the original URDF/FK. Run with the local
  `sharpa-retarget` Python environment (Pinocchio is required).
- `scripts/render_hd_comparisons.py`: renders all eight archived clips and
  comparison pairs using Isaac Sim 5.1 at 1920×1080. Pass case IDs from
  `_local/upgrade_20260928_v1/comparison_plan.json`; completed renders are never
  overwritten. This is an offline kinematic presentation render.
- `scripts/prepare_pick_held_start.py` and `scripts/render_pick_held_start.py`:
  create the isolated opening hold and rerender the stapler clip with the same
  HD setup. Run preparation with `sharpa-retarget` Python, rendering with
  Isaac Sim 5.1, then `scripts/install_pick_held_start.py` after visual review.
  Source hashes, the exact changed pose range, array equality checks, render
  report, retained original assets and browser checks are under
  `_local/pick_held_start_20260928_v1/`. Only `m056_poses[0:36]` is replaced
  by the original frame-36 transform; all other arrays and later poses match.
- `scripts/render_contact_closeups.py`: run with the same eight case IDs in
  Isaac Sim to fit the paired stills to their shared mesh bounds in camera space.
  Both states retain a common camera with 10% framing padding; no poses change.
- `scripts/install_hd_assets.py`: checks native dimensions, frame counts, hashes,
  and unchanged hardware clips; installs the new `*-1080p` videos and contact
  stills. Run after preparing the base assets and the eight HD renders.
- `_local/upgrade_20260928_v1/hd_asset_manifest_v2.json`: HD video provenance and the
  earlier comparison-image inventory. This directory retains page files, source ZIP
  verification, camera/frame records, and render logs. None are served publicly.
- `scripts/prepare_contact_details.py` and `scripts/render_contact_details.py`:
  select archived contact frames and render three candidate views for each of
  seven additional task details. Selection uses surface proximity in world
  meters (object transforms can contain scale), followed by visual review;
  the ranking is a presentation heuristic, not a success or penetration metric.
  All 28 visual parts of the selected hand remain visible in the scene.
- `scripts/install_contact_details.py`: installs the reviewed view per task,
  verifies the unchanged original cup/bottle images, and updates only comparison
  image links. `_local/contact_revision_20260928_v4/selected_details.json` records
  the first contact-detail selection. Six render sets are reused from v3
  after exact equality checks on all geometry/pose arrays; v4 renders the pick
  detail. The earlier gallery stills remain preserved.
- `scripts/prepare_contact_alternates.py`: prepares other archived EgoDex lint
  and scoop clips for visual selection. Use `render_contact_details.py
  --prepared-root _local/contact_alternates_20260928_v1` with the prepared case
  IDs to render them with the same colors, lighting and 1080p framing.
  `scripts/install_contact_alternates.py --lint lint_11 0 --scoop scoop_2238 0`
  installs the reviewed replacements. The earlier nine-slider inventory is
  `_local/contact_alternates_20260928_v1/selected_details.json`: lint uses frame
  250 of `lint_11`, scoop frame 37 of `scoop_2238`. Both use the complete right
  hand and unchanged tool poses; each pair shares its frame and camera.
  Previous website images and all six candidate view sets are preserved.
- `scripts/prepare_taco_contacts.py`: prepares archived rolling and brushing
  candidates. Render the shortlisted case IDs with
  `render_contact_details.py --prepared-root _local/taco_contact_additions_20260928_v1`.
  `scripts/install_taco_contacts.py --lint taco_07 -70 --brush taco_12 -70`
  installs the reviewed pairs and groups all five TACO tasks together.
  The final eleven-slider inventory, source frames, cameras and image hashes
  are in `_local/taco_five_tasks_20260928_v1/selected_details.json`.
  The earlier six-example selection and its rendered kettle images are retained
  in the additions archive; the duplicate pouring detail is not on the page.

All media are self-contained under `static/`; no links depend on the robotics
workspace, a local file server, NUC, OSS credentials, or remote compute hosts.
The original videos, figures, experiments, and hardware scripts are untouched.
See [THIRD_PARTY.md](THIRD_PARTY.md) for template licensing and attribution.
