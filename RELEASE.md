# Release Process

## Creating a Release

### Automatic Release (Recommended)

1. **Update CHANGELOG.md** with the release date
2. **Commit all changes**:
   ```bash
   git add .
   git commit -m "chore: prepare release v3.1.0"
   git push origin main
   ```

3. **Create and push tag**:
   ```bash
   git tag -a v3.1.0 -m "Release v3.1.0"
   git push origin v3.1.0
   ```

4. **GitHub Actions will automatically**:
   - Build the package
   - Run tests
   - Publish to PyPI (if PYPI_API_TOKEN is configured)
   - Create GitHub release with artifacts

### Manual Release via GitHub UI

1. Go to **Releases** → **Draft a new release**
2. Choose tag: `v3.1.0` (create new tag)
3. Release title: `Release v3.1.0`
4. Description: Copy from CHANGELOG.md
5. Check "Set as the latest release"
6. Click "Publish release"

### PyPI Publishing

To publish to PyPI, you need to:

1. **Create PyPI API token**:
   - Go to https://pypi.org/manage/account/token/
   - Create a new API token
   - Copy the token

2. **Add to GitHub Secrets**:
   - Go to repository Settings → Secrets and variables → Actions
   - Add new secret: `PYPI_API_TOKEN`
   - Paste the token value

3. **The workflow will automatically publish** when a release is created.

## Version Bumping

Update version in:
- `pyproject.toml` - `version = "3.1.0"`
- `app.py` - `app.setApplicationVersion("3.1.0")`
- `CHANGELOG.md` - Add new version section

## Release Checklist

- [ ] All tests passing
- [ ] CHANGELOG.md updated with release date
- [ ] Version numbers updated in all files
- [ ] Documentation reviewed
- [ ] Tag created and pushed
- [ ] GitHub release created
- [ ] PyPI package published (if applicable)
