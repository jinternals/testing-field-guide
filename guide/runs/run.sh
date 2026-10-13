#!/usr/bin/env bash
# Compiles main + tests and runs JUnit. Usage: ./run.sh [extra ConsoleLauncher args]
set -e
unset JAVA_TOOL_OPTIONS
J=${LIB:-/tmp/claude-0/lib2/jars}; CP=$(ls $J/*.jar | tr '\n' ':')
EX="--add-exports java.base/jdk.internal.org.objectweb.asm=ALL-UNNAMED --add-exports java.base/jdk.internal.org.objectweb.asm.commons=ALL-UNNAMED --add-exports java.base/jdk.internal.org.objectweb.asm.signature=ALL-UNNAMED"
rm -rf out && mkdir -p out/main out/test
javac -Xlint:all -Werror -d out/main $(find src/main -name "*.java")
javac -Xlint:all,-processing -d out/test -cp out/main:$CP $(find src/test -name "*.java")
java $EX -XX:+EnableDynamicAgentLoading -Xshare:off -cp $CP org.junit.platform.console.ConsoleLauncher execute \
  -cp out/main:out/test --select-package shop --disable-banner --disable-ansi-colors "$@"
