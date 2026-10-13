#!/usr/bin/env bash
unset JAVA_TOOL_OPTIONS
J=${LIB:-/tmp/claude-0/lib2/jars}; CP=$(ls $J/*.jar | tr '\n' ':')
EX="--add-exports java.base/jdk.internal.org.objectweb.asm=ALL-UNNAMED --add-exports java.base/jdk.internal.org.objectweb.asm.commons=ALL-UNNAMED --add-exports java.base/jdk.internal.org.objectweb.asm.signature=ALL-UNNAMED"
rm -rf out/fail && mkdir -p out/fail
javac -d out/fail -cp out/main:$CP $(find failing -name "*.java")
java $EX -XX:+EnableDynamicAgentLoading -Xshare:off -cp $CP org.junit.platform.console.ConsoleLauncher execute \
  -cp out/main:out/fail --select-class "$1" --disable-banner --disable-ansi-colors --details=tree --details-theme=ascii 2>&1 | grep -v self-attaching
