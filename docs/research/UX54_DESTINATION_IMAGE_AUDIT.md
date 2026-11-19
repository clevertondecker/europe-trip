# UX 5.4 — Destination image audit (2026-11-19)

## Scope: all 46 destinations in discovery
- **36 destinations** have bundled licensed 800×450 WebP assets under `assets/destinations/`. These are checked for file existence, image format, dimensions, non-trivial size, distinct checksums and attribution by existing offline tests.
- **10 destinations** use editorially registered Wikimedia Commons photos and are exposed to browser-side HTTP/CDN failures. IDs: `mulhouse`, `strasbourg`, `metz`, `nancy`, `colmar`, `freiburg`, `basel`, `luxembourg`, `interlaken`, `oeschinen`.
- There are 65 canonical attractions in `data/attractions_2027.json`, none with independent `photo` attributes. The destination card photograph is therefore not a per-attraction image guarantee.

## Findings
1. **Metz:** actual broken image in user screenshot, from `Special:FilePath` hotlink. Commons file page is indexed, but the browser photo failed.
2. **Other 9 editorial URLs:** same redirect-based loading risk. This is a structural susceptibility, *not* evidence that all nine are currently broken. The exact image byte responses were not exhaustively verifiable in this review.
3. **Local WebP 36:** existing tests validate integrity offline; there was no direct evidence of local file corruption. Do not replace these licensed assets.
4. **Other rendering surface:** UX 4.7 uses CSS-background images; it already has a neutral visual fallback but also used the redirect URLs. Route those through the same direct-URL resolver.

## Fix
- Resolve known Commons `Special:FilePath` source URLs to deterministic `upload.wikimedia.org` addresses, while **retaining the original source page for attribution**. The CDN address does not prove that every remote file is currently reachable.
- Prefer licensed bundled WebP bytes over hotlinked editorial photos **where the same destination has a local asset**; catalog data unchanged.
- Browser failures present a neutral placeholder rather than a broken-image icon, in both destination-discovery cards and the pre-existing UX 4.7 photo markup.
- Automated tests cover all 10 editorial entries, the existing 36 WebP files, the fallback and the read-only catalog.

## Remaining acceptance criteria
Browser-check all pages, including Metz, Strasbourg, Nancy, Colmar, Oeschinensee, and the remaining editorial-only destinations. For each, confirm the image really appears *or* the neutral fallback appears, and the author/license/source remain legible. Screenshots are required to claim 46/46 image display success; static source tests and a green CI do not prove live CDN availability.
