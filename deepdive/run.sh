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
java -XX:+PrintFlagsFinal -version 2>/dev/null | grep -E " (Tier3InvocationThreshold|Tier4InvocationThreshold|Tier3BackEdgeThreshold|Tier4BackEdgeThreshold|TieredStopAtLevel|CICompilerCount|ReservedCodeCacheSize|MaxInlineSize|FreqInlineSize|InlineSmallCode|MaxInlineLevel|TypeProfileWidth|TypeProfileMajorReceiverPercent|DoEscapeAnalysis|EliminateAllocations|ThreadStackSize|LockingMode) " | tee $L/jit-flags.txt
java -Xint -Dstdout.encoding=UTF-8 -cp $CP deep.jit.WarmUp | tee $L/warmup-xint.txt
java -XX:+PrintCompilation -cp $CP deep.jit.WarmUp | grep "sumOfSquares" | tee $L/warmup-compilation.txt
$J org.openjdk.jmh.Main DeadCodeBench -f 1 -wi 3 -w 1 -i 5 -r 1 2>&1 | tee $L/jmh-full.txt | tail -12
sed -n '/^Benchmark/,$p' $L/jmh-full.txt > $L/jmh.txt
# what C2 does to calls and allocations: inlining, receiver types, escape analysis (-prof gc: bytes allocated per op)
$J org.openjdk.jmh.Main InliningBench -f 1 -wi 3 -w 1 -i 5 -r 1 -prof gc 2>&1 | tee $L/jmh-inline-full.txt | tail -30
sed -n '/^Benchmark/,$p' $L/jmh-inline-full.txt > $L/jmh-inline.txt
java -XX:+UnlockDiagnosticVMOptions -XX:+PrintInlining -XX:-BackgroundCompilation -cp $CP deep.jit.CallSites \
  | grep -E "CallSites[$](Shape|A|B|C|D)::area" | awk '!seen[$0]++' | tee $L/jit-inlining.txt || true

echo "== 7 GC"
for gc in G1 ZGC; do
  flags=$([ $gc = G1 ] && echo "-XX:+UseG1GC" || echo "-XX:+UseZGC -XX:+ZGenerational")
  java $flags -Xms1g -Xmx1g -Xlog:gc,gc+phases:file=$L/gc-$gc.log -Dstdout.encoding=UTF-8 -cp $CP \
    deep.gc.GcLatency 15 | tee $L/gc-$gc.txt
done

# heap size: the G1 region size it chooses, and pauses at 4 GB against 1 GB
for h in 1g 4g 16g; do
  printf "%-6s " "-Xmx$h"; java -XX:+UseG1GC -Xmx$h -Xlog:gc+init -version 2>&1 | grep -o "Heap Region Size: .*"
done | tee $L/gc-init.txt
for gc in G1 ZGC; do
  flags=$([ $gc = G1 ] && echo "-XX:+UseG1GC" || echo "-XX:+UseZGC -XX:+ZGenerational")
  java $flags -Xms4g -Xmx4g -Xlog:gc,gc+phases:file=$L/gc-$gc-4g.log -Dstdout.encoding=UTF-8 -cp $CP \
    deep.gc.GcLatency 15 | tee $L/gc-$gc-4g.txt
done
# the same reference loads and stores under three collectors' barriers
: > $L/jmh-barrier.txt
for gc in "-XX:+UseParallelGC" "-XX:+UseG1GC" "-XX:+UseZGC -XX:+ZGenerational"; do
  echo "## $gc" | tee -a $L/jmh-barrier.txt
  $J org.openjdk.jmh.Main BarrierBench -f 1 -wi 3 -w 1 -i 5 -r 1 -jvmArgs "-Xms1g -Xmx1g $gc" 2>&1 \
    | sed -n '/^Benchmark/,$p' | tee -a $L/jmh-barrier.txt
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

: > $L/throttle.txt
for run in ":0" "--cpus=0.5:0" ":3" "--cpus=2:3" "--cpus=0.5:3"; do
  opts=${run%%:*}; burners=${run##*:}
  printf "%-22s " "docker run $opts" | tee -a $L/throttle.txt
  docker run --rm $opts -v "$PWD/src/main/java/deep/box:/p:ro" $img java /p/Throttle.java $burners 2>/dev/null | tee -a $L/throttle.txt
done

echo "== 11 Kafka"
docker run -d --rm --name kafka -p 9092:9092 apache/kafka:4.3.1 > /dev/null    # one broker, KRaft, image defaults
for i in $(seq 1 60); do docker logs kafka 2>&1 | grep -q "Kafka Server started" && break; sleep 1; done
for mode in producer fetch partitions pollinterval; do
  $J deep.kafka.KafkaLatency $mode 2> $L/kafka-$mode.err | tee $L/kafka-$mode.txt
done
docker logs kafka 2>&1 | grep -E "Kafka version|Kafka Server started" | head -3 > $L/kafka-broker.txt
docker stop kafka > /dev/null

echo "== 8 (cont.) where 10,000 blocked threads keep their stacks"
: > $L/vt-memory.txt
for m in platform virtual; do
  java -XX:NativeMemoryTracking=summary -cp $CP deep.vt.ThreadMemory $m | tee -a $L/vt-memory.txt
done

echo "== 1 (cont.) many small writes: Nagle, TCP_NODELAY, autocorking"
echo "tcp_autocorking $(cat /proc/sys/net/ipv4/tcp_autocorking)" | tee $L/smallwrites.txt
$J deep.tcp.SmallWrites | tee -a $L/smallwrites.txt
sudo sysctl -q -w net.ipv4.tcp_autocorking=0
echo "tcp_autocorking $(cat /proc/sys/net/ipv4/tcp_autocorking)" | tee -a $L/smallwrites.txt
$J deep.tcp.SmallWrites | tee -a $L/smallwrites.txt
sudo sysctl -q -w net.ipv4.tcp_autocorking=1

echo "== 10 memory model"
: > $L/staleflag.txt
for i in 1 2 3 4 5; do $J deep.jmm.StaleFlag | tee -a $L/staleflag.txt; done
$J org.openjdk.jmh.Main FenceBench -f 1 -wi 3 -w 1 -i 5 -r 1 2>&1 | sed -n '/^Benchmark/,$p' | tee $L/jmh-fence.txt
echo "== 3 (cont.) the background connect without a timeout"
wait $SYN || true; sleep 1
cat $L/syn.txt; awk '{print $3}' $L/syn-ss.txt | uniq -c | head -20
echo "done"
