package deep.tcp;

import java.io.BufferedOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.ServerSocket;
import java.net.Socket;
import java.util.concurrent.CountDownLatch;
import java.util.regex.Pattern;

/**
 * The case Nagle was designed for: a stream of tiny writes
 * with no reply to wait for. 10,000 one-byte writes to a
 * server that only reads. Once the server has every byte,
 * the client socket's own counter of data segments sent
 * (data_segs_out, from `ss -ti`) is read.
 */
public final class SmallWrites {
  static final int WRITES = 10_000;
  static final Pattern SEGS =
      Pattern.compile("data_segs_out:(\\d+)");

  public static void main(String[] args) throws Exception {
    System.out.printf("%,d writes of 1 byte, nothing sent"
        + " back except ACKs%n", WRITES);
    run("Nagle on (default)", false, false);
    run("TCP_NODELAY", true, false);
    run("BufferedOutputStream, one flush", false, true);
  }

  static void run(String name, boolean noDelay, boolean buffer)
      throws Exception {
    try (var server = new ServerSocket(0)) {
      var all = new CountDownLatch(1);
      var reader = Thread.ofPlatform()
          .start(() -> drain(server, all));
      long t0 = System.nanoTime();
      int port = server.getLocalPort();
      try (var s = new Socket("127.0.0.1", port)) {
        s.setTcpNoDelay(noDelay);
        OutputStream out = buffer
            ? new BufferedOutputStream(s.getOutputStream())
            : s.getOutputStream();
        for (int i = 0; i < WRITES; i++) {
          out.write('x');
        }
        out.flush();
        all.await();                   // the server has it all
        long ms = (System.nanoTime() - t0) / 1_000_000;
        String segs = dataSegsOut(s.getLocalPort());
        System.out.printf("%-34s %6d ms   data segments sent"
            + " by the client %7s%n", name, ms, segs);
        s.shutdownOutput();
        reader.join();
      }
    }
  }

  static void drain(ServerSocket server, CountDownLatch all) {
    try (Socket c = server.accept();
        InputStream in = c.getInputStream()) {
      byte[] buf = new byte[8192];
      long got = 0;
      int n;
      while ((n = in.read(buf)) >= 0) {
        got += n;
        if (got >= WRITES) {
          all.countDown();
        }
      }
    } catch (Exception e) {
      throw new RuntimeException(e);
    }
  }

  /** The kernel's per-socket counter, via `ss -tin`. */
  static String dataSegsOut(int localPort) throws Exception {
    Process p = new ProcessBuilder("ss", "-tinH",
        "sport = :" + localPort).redirectErrorStream(true)
        .start();
    String out = new String(p.getInputStream().readAllBytes());
    p.waitFor();
    var m = SEGS.matcher(out);
    return m.find()
        ? String.format("%,d", Long.parseLong(m.group(1)))
        : "n/a";
  }
}
