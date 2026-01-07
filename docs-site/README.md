# Waqt Documentation

This directory contains the source files for the Waqt documentation website, built with [MkDocs](https://www.mkdocs.org/) and the [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) theme.

## Documentation Site

The documentation is automatically published to GitHub Pages at:
**[https://gmouaad.github.io/waqt/](https://gmouaad.github.io/waqt/)**

## Local Development

### Prerequisites

- Python 3.11+
- pip or uv

### Setup

1. **Install MkDocs and dependencies:**

   ```bash
   pip install mkdocs mkdocs-material
   ```

2. **Build the documentation:**

   ```bash
   mkdocs build
   ```

3. **Serve the documentation locally:**

   ```bash
   mkdocs serve
   ```

   The documentation will be available at `http://localhost:8000`

### Live Reload

When you run `mkdocs serve`, the documentation site will automatically reload when you save changes to any documentation file.

## Structure

```
docs-site/
├── index.md              # Home page
├── installation.md       # Installation guide
├── usage.md             # Usage guide
├── build.md             # Building executables guide
├── dev-container.md     # Development container guide
├── e2e-testing.md       # E2E testing guide
├── mcp-guide.md         # MCP integration guide
├── uv-migration.md      # UV migration guide
├── contributing.md      # Contributing guide
└── license.md           # License
```

## Configuration

The site configuration is in `mkdocs.yml` at the repository root.

## Deployment

Documentation is automatically deployed to GitHub Pages when changes are pushed to the `main` branch. The deployment is handled by the GitHub Actions workflow at `.github/workflows/pages.yml`.

### Manual Deployment

To manually deploy:

```bash
mkdocs gh-deploy
```

This will build the documentation and push it to the `gh-pages` branch.

## Updating Documentation

1. Edit the relevant `.md` file in the `docs-site/` directory
2. Test locally with `mkdocs serve`
3. Commit and push your changes
4. GitHub Actions will automatically build and deploy the updated documentation

## Style Guide

- Use Markdown for all documentation
- Follow the [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/reference/) style guide
- Use admonitions for notes, warnings, and tips
- Use code blocks with language identifiers for syntax highlighting
- Keep links relative when referencing other documentation pages

## Resources

- [MkDocs Documentation](https://www.mkdocs.org/)
- [Material for MkDocs Documentation](https://squidfunk.github.io/mkdocs-material/)
- [Markdown Guide](https://www.markdownguide.org/)
