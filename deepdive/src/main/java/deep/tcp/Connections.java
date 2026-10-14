package deep.tcp;

import java.io.InputStream;
import java.net.InetAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.nio.file.Files;
import java.nio.file.Path;

/**
 * 2,000 request/response exchanges over one kept-alive
 * connection, then over a new connection each, closed first by
 * the client and then by the server. Counts TIME_WAIT sockets
 * in the kernel's own table, /proc/net/tcp (state 06).
 */
public final class Connections {
  static final int N = 2_000;
  static final InetAddress LO =
      InetAddress.getLoopbackAddress();

  public static void main(String[] args) throws Exception {
    System.out.println("ip_local_port_range: "
        + sysctl("net/ipv4/ip_local_port_range"));
    System.out.println("tcp_tw_reuse:        "
        + sysctl("net/ipv4/tcp_tw_reuse"));
    keepAlive();
    perRequest(true);
    perRequest(false);
  }

  static void keepAlive() throws Exception {
    try (var server = new ServerSocket(0, 512, LO)) {
      Thread.ofPlatform().daemon().start(() -> echoAll(server));
      long t0 = System.nanoTime();
      try (var s = new Socket(LO, server.getLocalPort())) {
        s.setTcpNoDelay(true);
        for (int i = 0; i < N; i++) {
          s.getOutputStream().write(new byte[100]);
          s.getInputStream().readNBytes(100);
        }
      }
      report("one kept-alive connection", t0, server, -1);
    }
  }

  static void perRequest(boolean clientClosesFirst)
      throws Exception {
    try (var server = new ServerSocket(0, 512, LO)) {
      int port = server.getLocalPort();
      Thread.ofPlatform().daemon().start(
          () -> oneEach(server, !clientClosesFirst));
      long t0 = System.nanoTime();
      for (int i = 0; i < N; i++) {
        try (var s = new Socket(LO, port)) {
          s.setTcpNoDelay(true);
          s.getOutputStream().write(new byte[100]);
          InputStream in = s.getInputStream();
          in.readNBytes(100);
          if (!clientClosesFirst) {
            in.read();          // wait for the server's FIN
          }
        }
      }
      Thread.sleep(200);
      report(clientClosesFirst ? "new connection, client closes"
          : "new connection, server closes", t0, server, port);
    }
  }

  static void report(String name, long t0, ServerSocket server,
      int port) throws Exception {
    double us = (System.nanoTime() - t0) / 1e3 / N;
    String tw = port < 0 ? "" : String.format(
        "   TIME_WAIT: client side %d, server side %d",
        timeWait(port, false), timeWait(port, true));
    System.out.printf("%-31s %7.1f µs per request%s%n",
        name, us, tw);
  }

  /**
   * TIME_WAIT entries whose local (or remote) port is port.
   * A dual-stack JVM's sockets are listed in tcp6, as
   * ::ffff:127.0.0.1, so read both tables.
   */
  static long timeWait(int port, boolean local)
      throws Exception {
    String hex = String.format(":%04X", port);
    long n = 0;
    for (String table : new String[] {"tcp", "tcp6"}) {
      Path p = Path.of("/proc/net/" + table);
      if (!Files.exists(p)) {
        continue;                   // no IPv6 on this machine
      }
      n += Files.readAllLines(p).stream()
          .skip(1).map(l -> l.trim().split("\\s+"))
          .filter(f -> f[3].equals("06"))
          .filter(f -> (local ? f[1] : f[2]).endsWith(hex))
          .count();
    }
    return n;
  }

  static String sysctl(String key) throws Exception {
    // /proc files report size 0: read lines, not a sized buffer
    return String.join(" ", Files.readAllLines(
        Path.of("/proc/sys/" + key))).replace('\t', ' ').trim();
  }

  static void echoAll(ServerSocket server) {
    try (Socket c = server.accept()) {
      c.setTcpNoDelay(true);
      byte[] b;
      var in = c.getInputStream();
      while ((b = in.readNBytes(100)).length == 100) {
        c.getOutputStream().write(b);
      }
    } catch (Exception e) {
      // done
    }
  }

  static void oneEach(ServerSocket server,
      boolean serverCloses) {
    while (!server.isClosed()) {
      try (Socket c = server.accept()) {
        c.setTcpNoDelay(true);
        var in = c.getInputStream();
        c.getOutputStream().write(in.readNBytes(100));
        if (!serverCloses) {
          in.read();            // wait for the client's FIN
        }
      } catch (Exception e) {
        // server closed
      }
    }
  }
}
