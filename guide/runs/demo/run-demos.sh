#!/usr/bin/env bash
# Reproduces the TDD red step and the hand-made mutation-testing demo.
unset JAVA_TOOL_OPTIONS
cd "$(dirname "$0")/.."
J=${LIB:-/tmp/claude-0/lib2/jars}; CP=$(ls $J/*.jar | tr '\n' ':')
EX="--add-exports java.base/jdk.internal.org.objectweb.asm=ALL-UNNAMED --add-exports java.base/jdk.internal.org.objectweb.asm.commons=ALL-UNNAMED --add-exports java.base/jdk.internal.org.objectweb.asm.signature=ALL-UNNAMED"
run() { java $EX -XX:+EnableDynamicAgentLoading -Xshare:off -cp $CP org.junit.platform.console.ConsoleLauncher execute --disable-banner --disable-ansi-colors --details=tree --details-theme=ascii "$@" 2>&1 | grep -v self-attaching; }
rm -rf out/demo && mkdir -p out/demo/{tdd,orig,mutant,tests}
echo "===== TDD step 1 (red) ====="
javac -d out/demo/tdd -cp $CP demo/tdd/shop/PasswordPolicy.java src/test/java/shop/PasswordPolicyTest.java
run -cp out/demo/tdd --select-class shop.PasswordPolicyTest | sed -n '1,30p'
echo "===== Weak tests vs ORIGINAL code ====="
javac -d out/demo/orig $(find src/main -name "*.java")
javac -d out/demo/tests -cp out/demo/orig:$CP demo/weak/shop/WeakDiscountPolicyTest.java src/test/java/shop/DiscountPolicyTest.java
run -cp out/demo/orig:out/demo/tests --select-class shop.WeakDiscountPolicyTest | tail -14 | head -3
echo "===== MUTANT: weak tests ====="
javac -d out/demo/mutant $(find src/main -name "*.java" ! -name DiscountPolicy.java) demo/mutant/shop/DiscountPolicy.java
run -cp out/demo/mutant:out/demo/tests --select-class shop.WeakDiscountPolicyTest | sed -n '1,8p'
echo "===== MUTANT: boundary tests ====="
run -cp out/demo/mutant:out/demo/tests --select-class shop.DiscountPolicyTest | sed -n '1,14p'
