# GitHub repository, Pages and SEO setup

Canonical repository: https://github.com/modassarislam37/funnel-engineering-system-github-ready-v5

## Publish the documentation site

The paper-style, responsive static site lives in `docs/index.html`. It needs no Node dependencies or build system.

1. Review source files and ensure the repository contains no private material.
2. Make the repository **public** using GitHub **Settings → General → Danger Zone → Change repository visibility**. This step requires repository admin permissions and is not performed by the site code.
3. Open **Settings → Pages** and configure **Deploy from a branch**, branch `main`, folder `/docs`; save.
4. Check the **Actions** tab for the Pages deployment, then verify the live site:
   https://modassarislam37.github.io/funnel-engineering-system-github-ready-v5/
5. Confirm `robots.txt`, `sitemap.xml`, canonical URLs and page metadata resolve publicly. GitHub controls indexing; SEO metadata does not guarantee search placement.

**Note:** Pages deployment from a private repository may depend on your GitHub plan and organizational settings. This repository's current visibility was private when the site was prepared.

## Paper UI structure

- `docs/index.html`: semantic, accessible landing page
- `docs/assets/site.css`: warm paper design tokens, responsive layout and reduced-motion support
- `docs/assets/site.js`: local command-selector behavior only; no tracking, cookies or network calls
- `docs/assets/fes-mark.svg`: vector brand mark
- `docs/sitemap.xml`: site URL for crawlers
- `docs/robots.txt`: crawler policy
- `docs/404.html`: branded error page
- `docs/.nojekyll`: publish files as-is

## GitHub discoverability

Repository owners can set these manually on the repo's **About** area:

**Description:** Open-source AI coding agent skills for bug fixing, vibe-code rescue, security review and evidence-gated software engineering.

**Suggested topics:** `ai-agents`, `agent-skills`, `coding-agents`, `vibe-coding`, `software-engineering`, `ai-code-review`, `security-audit`, `codex`, `claude-code`, `cursor`

**Website:** https://modassarislam37.github.io/funnel-engineering-system-github-ready-v5/

Use accurate descriptions and avoid unsupported claims such as “fixes all vulnerabilities.”

## SEO maintenance

Keep `docs/index.html` canonical URL, Open Graph URL, sitemap URL, and README website link synchronized if the repository name or domain changes. The project is currently named `funnel-engineering-system-github-ready-v5`; old publishing instructions targeting `funnel-engineering-system` are obsolete for this release.

Contributions require tests and safety checks. Never place API tokens in public HTML or GitHub history.
