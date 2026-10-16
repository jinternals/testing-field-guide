package deep.tcp;

import java.io.BufferedOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.ServerSocket;
import java.net.Socket;
import java.nio.file.Files;
import java.nio.file.Path;

/**
 * The case Nagle was designed for: a stream of tiny writes
 * with no reply to wait for. 10,000 one-byte writes to a
 * server that only reads. Segments are counted from the
 * kernel's own counter (Tcp OutSegs in /proc/net/snmp).
 */
public final class SmallWrites {
  static final int WRITES = 10_000;

  public static void main(String[] args) throws Exception {
    System.out.printf("%,d writes of 1 byte, nothing sent back"
        + " except ACKs%n", WRITES);
    run("Nagle on (default)", false, false);
    run("TCP_NODELAY", true, false);
    run("BufferedOutputStream, one flush", false, true);
  }

  static void run(String name, boolean noDelay, boolean buffer)
      throws Exception {
    try (var server = new ServerSocket(0)) {
      var reader =
          Thread.ofPlatform().start(() -> drain(server));
      long segs0 = outSegs();
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
        s.shutdownOutput();
        reader.join();
      }
      long ms = (System.nanoTime() - t0) / 1_000_000;
      System.out.printf("%-34s %6d ms   segments sent by the"
          + " host %,7d%n", name, ms, outSegs() - segs0);
    }
  }

  static void drain(ServerSocket server) {
    try (Socket c = server.accept();
        InputStream in = c.getInputStream()) {
      byte[] buf = new byte[8192];
      while (in.read(buf) >= 0) {
        // discard
      }
    } catch (Exception e) {
      throw new RuntimeException(e);
    }
  }

  /** Tcp: OutSegs, all TCP segments the host has sent. */
  static long outSegs() throws Exception {
    var lines = Files.readAllLines(Path.of("/proc/net/snmp"));
    for (int i = 0; i < lines.size() - 1; i++) {
      if (lines.get(i).startsWith("Tcp:")
          && lines.get(i + 1).startsWith("Tcp:")) {
        String[] names = lines.get(i).split("\\s+");
        String[] vals = lines.get(i + 1).split("\\s+");
        for (int k = 0; k < names.length; k++) {
          if (names[k].equals("OutSegs")) {
            return Long.parseLong(vals[k]);
          }
        }
      }
    }
    return -1;
  }
}
