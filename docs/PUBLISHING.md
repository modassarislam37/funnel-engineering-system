# Publishing to GitHub

The release is designed for the public repository:

https://github.com/modassarislam37/funnel-engineering-system

This package includes a safe, one-command publication script for **an empty repository**.
It uses your existing Git credentials and publishes all source files with their folders intact.

## Steps on macOS or Linux

1. Install Git and authenticate with GitHub (`gh auth login` or Git Credential Manager).
2. Extract the package and open Terminal in `funnel-engineering-system-github-ready-v5`.
3. Run the checks:

```bash
python3 tools/validate_package.py
python3 -m unittest discover -s tests -v
python3 tools/publish_to_github.py --dry-run
```

4. Publish all source files:

```bash
python3 tools/publish_to_github.py
```

The script **refuses to push to a nonempty repository**, never force-pushes and does not
change your existing projects. If Git reports your name/email is missing, configure those
in Git before retrying. No access token is needed in the URL or command line.

After the push, inspect the repository Code tab for `skills/`, `tools/`, `tests/`,
`docs/`, `codex/`, and `.github/`, and review the Actions tab for CI status.
The automated tests check the framework itself, not every possible AI agent or target app.
