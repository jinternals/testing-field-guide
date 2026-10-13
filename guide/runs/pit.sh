#!/usr/bin/env bash
# Runs PIT 1.30.0 (+ pitest-junit5-plugin 1.2.3) on the shop example. Extra PIT options can be appended.
unset JAVA_TOOL_OPTIONS
J=${LIB:-/tmp/claude-0/lib2/jars}; CP=$(ls $J/*.jar | tr '\n' ':')
EXA="--add-exports=java.base/jdk.internal.org.objectweb.asm=ALL-UNNAMED,--add-exports=java.base/jdk.internal.org.objectweb.asm.commons=ALL-UNNAMED,--add-exports=java.base/jdk.internal.org.objectweb.asm.signature=ALL-UNNAMED,--add-exports=java.base/jdk.internal.org.objectweb.asm.tree=ALL-UNNAMED,--add-exports=java.base/jdk.internal.org.objectweb.asm.util=ALL-UNNAMED,-XX:+EnableDynamicAgentLoading"
java $(echo $EXA | tr ',' ' ') -cp $CP:out/main:out/test org.pitest.mutationtest.commandline.MutationCoverageReport \
  --reportDir pit-reports --targetClasses 'shop.*' --excludedClasses 'shop.*Test,shop.*Test$*' \
  --targetTests 'shop.*Test' --sourceDirs src/main/java \
  --classPath "$(echo $CP | tr ':' ',')out/main,out/test" --outputFormats XML,CSV --timestampedReports=false \
  --jvmArgs "$EXA" --threads 2 "$@" 2>&1 | grep -v "self-attaching"
