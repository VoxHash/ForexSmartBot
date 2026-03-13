#!/bin/bash
# Script to create a release for ForexSmartBot

set -e

VERSION=${1:-"3.1.0"}
TAG="v${VERSION}"

echo "Creating release ${TAG}..."

# Check if tag already exists
if git rev-parse "${TAG}" >/dev/null 2>&1; then
    echo "Tag ${TAG} already exists!"
    exit 1
fi

# Check if we're on main/master branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [[ "$CURRENT_BRANCH" != "main" && "$CURRENT_BRANCH" != "master" ]]; then
    echo "Warning: Not on main/master branch. Current branch: ${CURRENT_BRANCH}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo "Warning: You have uncommitted changes!"
    git status --short
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create tag
echo "Creating tag ${TAG}..."
git tag -a "${TAG}" -m "Release ${TAG}

See CHANGELOG.md for details."

# Push tag
echo "Pushing tag to remote..."
git push origin "${TAG}"

echo ""
echo "✅ Release ${TAG} created and pushed!"
echo ""
echo "Next steps:"
echo "1. GitHub Actions will automatically build and create the release"
echo "2. If PYPI_API_TOKEN is configured, the package will be published to PyPI"
echo "3. Check the Actions tab for build status"
echo ""
echo "To create the release manually via GitHub UI:"
echo "  https://github.com/VoxHash/ForexSmartBot/releases/new?tag=${TAG}"
