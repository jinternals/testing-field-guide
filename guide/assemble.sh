#!/usr/bin/env bash
# Builds guide/java: the repository's code, the hand-run scripts, and the
# CI logs from the ci-logs-* branches. regenerate.sh then writes every hand-run output.
# Run from the repository root.
set -euo pipefail
G=guide; W=$G/java
rm -rf "$W" && mkdir -p "$W/ci-logs"
cp -r src pom.xml build.gradle.kts settings.gradle.kts gradlew gradle README.md extras spring spring-auth .github "$W/"
cp -r $G/runs/. "$W/"

mv "$W/ci-static/"* "$W/ci-logs/" && rmdir "$W/ci-static"

git fetch -q origin '+refs/heads/ci-logs-*:refs/remotes/origin/ci-logs-*'
take() {   # take <branch> <path in branch> <dest under ci-logs>
  mkdir -p "$W/ci-logs/$3"
  git archive "origin/ci-logs-$1" "$2" | tar -x -C "$W/ci-logs/$3" --strip-components=$(($(tr -cd / <<<"$2" | wc -c) + 1))
}
take maven   logs        maven
take gradle  logs        gradle
take spring  spring/logs spring
take extras  logs        extras
take shard-1 logs        shard-1
take shard-2 logs        shard-2
echo "assembled $(find "$W" -type f | wc -l) files in $W"
