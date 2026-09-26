# EgoCPT project website

Static research project page based on the **original NeRFies template**:
<https://nerfies.github.io/>. No framework, package installation, tracking,
external JavaScript, or build service is required to view it.

## Content

- Title and abstract: the author's final `ICRA_Submission (12).pdf`, not the
  older LaTeX working copy.
- Authors, in the user-confirmed order: Zhixin Sun*, Kairui Shi, Tianao Ren,
  Ming Yang, Mark Cutkosky, James Jingxi Xu.
- Tianao Ren and Mark Cutkosky: Stanford University. All other authors:
  Ant Group. No affiliations inferred from another project's website.
- Header logos: the exact Ant Group and Stanford PNGs used by
  <https://ume-exo.github.io/>, as requested. Original artwork and colors are
  unchanged; local copies work without third-party image requests. Hashes and
  sources are recorded in `static/logos/provenance.json` and checked on deploy.
- The star after Zhixin Sun is retained exactly as supplied. Its meaning has
  not been supplied; the page does not invent an equal-contribution or
  corresponding-author note.
- Paper PDF, latest approved light supplementary video (cut 16), three real
  robot clips, method figure, contact comparisons, EgoDex/TACO examples.
- Hardware clips use the approved continuous 1x windows: pouring [1,11)s,
  lint rolling [4,10)s, sweeping [12.5,18.5)s. No trials are spliced.
- The stapler example keeps only frames 0–89, before hand release.
- Hardware replay with right-hand glove control and reconstructed-reference
  visualization are labeled separately; the page does not relabel either as
  new autonomous policy evaluation.

## Preview

From this directory:

```bash
node scripts/verify_site.mjs
node scripts/serve.mjs
```

Open <http://localhost:8765/> (forward port 8765 in VS Code when using SSH).
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

The author confirmed publication to the existing `Applewonder/EgoCPT.github.io`
repository on 2026-09-24. Its **project-site** URL is:

<https://applewonder.github.io/EgoCPT.github.io/>

The canonical and social-sharing URLs point to this project site, not to
`egocpt.github.io`. No custom domain or CNAME is configured.

1. The author has approved publishing to this repository. The included final
   PDF is still the anonymous submission, and the author star is preserved
   without inventing its meaning.
2. In the repository's **Settings → Pages**, set **Source → GitHub Actions**.
3. Commit these website files and push `main`. The included Pages workflow
   validates local assets, packages only `index.html`, `static/`, `.nojekyll`,
   and `THIRD_PARTY.md`, then deploys the site.
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
the code badge explicitly says "coming soon" instead of linking to a wrong repo.

Official deployment documentation:
<https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages>

## Edit and regenerate

- `index.html`: title, authors, affiliations, abstract, captions, links, BibTeX.
- `static/css/site.css`: responsive overrides on the original Bulma/NeRFies CSS.
- `static/js/site.js`: comparison sliders, view-aware video playback, citation copy.
- `scripts/prepare_assets.mjs`: optional, local-workspace media preparation;
  requires Node, FFmpeg, and the original project files. Do not run it on an
  already populated asset directory: derived files are not overwritten.
- `_local/asset_manifest.json`: local-only SHA-256, sizes, exact sources and trims.
  It is ignored by Git and excluded from the deployment artifact.

All media are self-contained under `static/`; no links depend on the robotics
workspace, a local file server, NUC, OSS credentials, or remote compute hosts.
The original videos, figures, experiments, and hardware scripts are untouched.
See [THIRD_PARTY.md](THIRD_PARTY.md) for template licensing and attribution.
