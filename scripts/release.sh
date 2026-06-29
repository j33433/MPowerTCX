#!/usr/bin/env bash
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Usage: scripts/release.sh <version>"
  echo "Example: scripts/release.sh 3.1.3"
  exit 1
fi

VERSION="$1"
TAG="v${VERSION}"
INDEX="web/index.html"

cd "$(dirname "$0")/.."

if git tag -l "$TAG" | grep -q .; then
  echo "Error: tag $TAG already exists"
  exit 1
fi

sed -i "s/v[0-9]\+\.[0-9]\+\.[0-9]\+<\/p>/v${VERSION}<\/p>/" "$INDEX"

git add "$INDEX"
git commit -m "Bump version to ${VERSION}"
git tag "$TAG"

echo ""
echo "Done. Push with:"
echo "  git push origin master $TAG"
