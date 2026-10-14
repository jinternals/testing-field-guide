#!/usr/bin/env bash
# Runs every deep-dive experiment and writes its output to ../logs (CI keeps them).
# Needs Linux, JDK 21, Maven, Docker, and sudo for tcpdump and iptables (a GitHub runner has all).
set -euo pipefail
cd "$(dirname "$0")"
L=../logs; mkdir -p $L
mvn -B -ntp -q compile org.apache.maven.plugins:maven-dependency-plugin:3.11.0:build-classpath -Dmdep.outputFile=cp.txt
CP=target/classes:$(cat cp.txt)
J="java -Dstdout.encoding=UTF-8 -cp $CP"

echo "== the machine"
{ echo "kernel $(uname -r)"; echo "cpus $(nproc)"; lscpu | grep -m1 "Model name" | sed 's/  */ /g'
  java -version 2>&1 | head -1
  for k in ip_local_port_range tcp_tw_reuse tcp_syn_retries tcp_pingpong_thresh tcp_fin_timeout; do
    printf "%-22s %s\n" "$k" "$(tr '\t' ' ' < /proc/sys/net/ipv4/$k)"; done
  grep -E "^CONFIG_HZ=" /boot/config-$(uname -r) || true; } | tee $L/machine.txt

echo "== 1 Nagle, delayed ACK"
$J deep.tcp.Nagle | tee $L/nagle.txt
sudo tcpdump -i lo -nn -l -ttttt -c 30 'tcp port 18080' > $L/nagle-trace.txt 2> /dev/null &
sleep 2; $J deep.tcp.Nagle trace; sleep 1; sudo pkill tcpdump || true; wait || true
cat $L/nagle-trace.txt

echo "== 2 connections"
$J deep.tcp.Connections | tee $L/connections.txt

echo "== 3 timeouts"
sudo iptables -A OUTPUT -d 192.0.2.1 -j DROP           # packets to it vanish: no reply, no refusal
# in the background: connect() with no timeout, and the kernel's SYN retransmission count each second
$J deep.tcp.SynRetries > $L/syn.txt &
SYN=$!
( start=$(date +%s); while kill -0 $SYN 2>/dev/null; do
    echo "$(( $(date +%s) - start )) s  $(ss -tno state syn-sent 'dst 192.0.2.1' | tail -n +2 | grep -o 'timer:([^)]*)')"
    sleep 1; done ) > $L/syn-ss.txt &
$J deep.tcp.Timeouts | tee $L/timeouts.txt

echo "== 4 pools"
$J deep.pool.PoolSize | tee $L/pool.txt
$J deep.pool.CpuPool | tee $L/cpupool.txt

echo "== 5 coordinated omission"
$J deep.latency.CoordinatedOmission | tee $L/co.txt

echo "== 6 JIT"
$J deep.jit.WarmUp | tee $L/warmup.txt
java -Xint -Dstdout.encoding=UTF-8 -cp $CP deep.jit.WarmUp | tee $L/warmup-xint.txt
java -XX:+PrintCompilation -cp $CP deep.jit.WarmUp | grep "sumOfSquares" | tee $L/warmup-compilation.txt
$J org.openjdk.jmh.Main DeadCodeBench -f 1 -wi 3 -w 1 -i 5 -r 1 2>&1 | tee $L/jmh-full.txt | tail -12
sed -n '/^Benchmark/,$p' $L/jmh-full.txt > $L/jmh.txt

echo "== 7 GC"
for gc in G1 ZGC; do
  flags=$([ $gc = G1 ] && echo "-XX:+UseG1GC" || echo "-XX:+UseZGC -XX:+ZGenerational")
  java $flags -Xms1g -Xmx1g -Xlog:gc,gc+phases:file=$L/gc-$gc.log -Dstdout.encoding=UTF-8 -cp $CP \
    deep.gc.GcLatency 15 | tee $L/gc-$gc.txt
done

echo "== 8 virtual threads"
java -Djdk.tracePinnedThreads=short -Dstdout.encoding=UTF-8 -cp $CP deep.vt.VirtualThreads 2>&1 \
  | awk '!seen[$0]++' | tee $L/vt.txt

echo "== 9 containers"
img=eclipse-temurin:21-jdk; docker pull -q $img > /dev/null
: > $L/containers.txt
for opts in "" "--cpus=2 --memory=2g" "--cpus=1 --memory=1g" "--cpus=0.5 --memory=512m"; do
  printf "%-48s " "docker run $opts" | tee -a $L/containers.txt
  docker run --rm $opts -v "$PWD/src/main/java/deep/box:/p:ro" $img java /p/Resources.java 2>/dev/null | tee -a $L/containers.txt
done
for flags in "-XX:ActiveProcessorCount=4" "-XX:MaxRAMPercentage=75"; do
  printf "%-48s " "docker run --cpus=1 --memory=1g … java $flags" | tee -a $L/containers.txt
  docker run --rm --cpus=1 --memory=1g -v "$PWD/src/main/java/deep/box:/p:ro" $img \
    java $flags /p/Resources.java 2>/dev/null | tee -a $L/containers.txt
done

echo "== 10 memory model"
: > $L/staleflag.txt
for i in 1 2 3 4 5; do $J deep.jmm.StaleFlag | tee -a $L/staleflag.txt; done
echo "== 3 (cont.) the background connect without a timeout"
wait $SYN || true; sleep 1
cat $L/syn.txt; awk '{print $3}' $L/syn-ss.txt | uniq -c | head -20
echo "done"
