#!/usr/bin/env bash
# Unit and integration coverage with the JaCoCo 0.8.15 agent, then a merged report.
set -e; unset JAVA_TOOL_OPTIONS
J=${LIB:-/tmp/claude-0/lib2/jars}; CP=$(ls $J/*.jar | tr '\n' ':')
AG=${JACOCO_AGENT:-/tmp/claude-0/lib2/jacocoagent.jar}   # -javaagent
JC=${JACOCO_API:-$AG}                                     # core + report API
EX="--add-exports java.base/jdk.internal.org.objectweb.asm=ALL-UNNAMED --add-exports java.base/jdk.internal.org.objectweb.asm.commons=ALL-UNNAMED --add-exports java.base/jdk.internal.org.objectweb.asm.signature=ALL-UNNAMED --add-exports java.base/jdk.internal.org.objectweb.asm.tree=ALL-UNNAMED"
run() { java $EX -XX:+EnableDynamicAgentLoading -javaagent:$AG=destfile=$1,includes=shop.* -cp $CP \
        org.junit.platform.console.ConsoleLauncher execute -cp out/main:out/test --select-package shop \
        --disable-banner --details=summary --disable-ansi-colors "${@:2}" 2>&1 | grep -E "tests (successful|failed)"; }
rm -rf coverage && mkdir -p coverage out/tools
javac -d out/tools -cp out/main:$JC scripts/CoverageSummary.java 2>&1 | grep -v JAVA_TOOL || true
echo "== unit tests (everything except *Api*Test)"; run coverage/unit.exec --exclude-classname '.*Api.*Test'
echo "== integration tests (OrderApi*Test)";        run coverage/it.exec   --include-classname '.*Api.*Test'
S() { java $EX -cp $JC:out/tools:out/main shop.CoverageSummary out/main src/main/java "$@" 2>&1 | grep -v JAVA_TOOL; }
echo; echo "== UNIT";        S coverage/html-unit coverage/unit.exec
echo; echo "== INTEGRATION"; S coverage/html-it   coverage/it.exec
echo; echo "== MERGED";      S coverage/html      coverage/unit.exec coverage/it.exec
