#!/usr/bin/env bash
# Re-runs every hand-run example in the guide and rewrites its output files.
# Needs: JDK 21, Maven. Run from the assembled workspace (guide/java).
set -euo pipefail
HERE=$(pwd)
if [ -z "${LIB:-}" ]; then   # CI: fetch the official jars; locally, pass LIB/JACOCO_AGENT/JACOCO_API to reuse yours
  mvn -B -ntp -q -f lib/pom.xml dependency:copy-dependencies -DoutputDirectory=$HERE/lib/jars
  mvn -B -ntp -q dependency:copy -Dartifact=org.jacoco:org.jacoco.agent:0.8.15:jar:runtime -DoutputDirectory=$HERE/lib/jacoco -Dmdep.stripVersion=true
  mvn -B -ntp -q -f lib/jacoco-api/pom.xml dependency:copy-dependencies -DoutputDirectory=$HERE/lib/jacoco-api/jars
  export LIB=$HERE/lib/jars
  export JACOCO_AGENT=$HERE/lib/jacoco/org.jacoco.agent-runtime.jar
  export JACOCO_API=$(ls $HERE/lib/jacoco-api/jars/*.jar | paste -sd: -)
fi
CP=$(ls $LIB/*.jar | tr '\n' ':')
EX="--add-exports java.base/jdk.internal.org.objectweb.asm=ALL-UNNAMED"

echo "== unit suite";      ./run.sh --details=tree --details-theme=unicode > suite-output.txt 2>&1 || true
echo "== failing demos";   ./runfail.sh shop.FailingExamplesTest > failing-output.txt 2>&1 || true
echo "== TDD/mutant demo"; bash demo/run-demos.sh > demo-output.txt 2>&1 || true
echo "== coverage";        ./coverage.sh > coverage-output.txt 2>&1
test -f coverage/html-unit/shop/index.html || { cat coverage-output.txt; exit 1; }

echo "== PIT: STRONGER";   ./pit.sh --mutators STRONGER > pit-output-stronger.txt 2>&1
echo "== PIT: before the fix (without OrderApiLifecycleTest)"
./pit.sh --excludedTestClasses shop.OrderApiLifecycleTest > pit-output-before.txt 2>&1
cp pit-reports/mutations.csv pit-mutations-before.csv
echo "== PIT: final, full mutation matrix"
./pit.sh --fullMutationMatrix=true > pit-output.txt 2>&1
javac -d out/tools src/tools/shop/RedundantTests.java
java -Dstdout.encoding=UTF-8 -cp out/tools shop.RedundantTests pit-reports/mutations.xml > redundancy-java.txt

echo "== load: Nagle on, then off"
javac -d out/load -cp out/main src/tools/shop/LoadSmoke.java
: > load-output.txt; : > load-output-nodelay.txt
for u in 1 10 50; do java -cp out/main:out/load shop.LoadSmoke $u >> load-output.txt; echo >> load-output.txt; done
for u in 1 50; do java -Dsun.net.httpserver.nodelay=true -cp out/main:out/load shop.LoadSmoke $u >> load-output-nodelay.txt; echo >> load-output-nodelay.txt; done

echo "== sequential vs parallel"
{ echo "# cpus: $(nproc)"; echo "# sequential"
  for i in 1 2 3; do ./run.sh --details=summary 2>&1 | grep "Test run finished"; done
  echo "# parallel (config/junit-platform.properties on the classpath)"
  for i in 1 2 3; do ./run.sh --details=summary -cp config 2>&1 | grep -E "Test run finished|tests successful"; done
} > parallel-output.txt

echo "== PMD CPD and the no-assert rule (PMD 7.17.0)"
curl -sSL -o /tmp/pmd.zip https://github.com/pmd/pmd/releases/download/pmd_releases%2F7.17.0/pmd-dist-7.17.0-bin.zip
unzip -q -o /tmp/pmd.zip -d /tmp && P=/tmp/pmd-bin-7.17.0/bin/pmd
{ for t in 100 50 25; do echo "### pmd cpd --minimum-tokens $t --dir src --language java"
    rc=0; out=$($P cpd --minimum-tokens $t --dir src --language java 2>&1) || rc=$?
    grep -c "^Found" <<<"$out" || true
    echo "exit code: $rc"; done; } > cpd-output.txt
R=category/java/bestpractices.xml/UnitTestShouldIncludeAssert
{ echo "$ pmd check -d src/test/java -d src/it/java -R …/UnitTestShouldIncludeAssert"
  $P check -d src/test/java -d src/it/java -R $R -f text 2>/dev/null && echo "(no violations, exit code 0)"
  echo; echo "$ pmd check -d demo/pmd -R …/UnitTestShouldIncludeAssert"
  $P check -d demo/pmd -R $R -f text 2>/dev/null | sed "s#$HERE/##"; echo "exit code ${PIPESTATUS[0]}"; } > pmd-asserts-output.txt || true
echo "done"
