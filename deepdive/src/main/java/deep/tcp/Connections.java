package deep.tcp;

import java.net.InetAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

/**
 * Request/response over one kept-alive connection, then over a
 * new connection each time, closed four ways. Afterwards it
 * counts sockets by state in the kernel's own tables,
 * /proc/net/tcp and tcp6: 05 = FIN_WAIT2, 06 = TIME_WAIT,
 * 08 = CLOSE_WAIT.
 */
public final class Connections {
  static final int N = 2_000;
  static final InetAddress LO =
      InetAddress.getLoopbackAddress();

  enum Close {
    CLIENT_FIRST, SERVER_FIRST, CLIENT_RESET, SERVER_NEVER
  }

  public static void main(String[] args) throws Exception {
    System.out.println("ip_local_port_range: "
        + sysctl("net/ipv4/ip_local_port_range"));
    System.out.println("tcp_tw_reuse:        "
        + sysctl("net/ipv4/tcp_tw_reuse"));
    keepAlive();
    for (Close c : Close.values()) {
      perRequest(c);
    }
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
      report("one kept-alive connection", t0, -1);
    }
  }

  static void perRequest(Close how) throws Exception {
    try (var server = new ServerSocket(0, 512, LO)) {
      int port = server.getLocalPort();
      Thread.ofPlatform().daemon()
          .start(() -> oneEach(server, how));
      long t0 = System.nanoTime();
      for (int i = 0; i < N; i++) {
        try (var s = new Socket(LO, port)) {
          s.setTcpNoDelay(true);
          if (how == Close.CLIENT_RESET) {
            s.setSoLinger(true, 0);       // close() sends RST
          }
          s.getOutputStream().write(new byte[100]);
          var in = s.getInputStream();
          in.readNBytes(100);
          if (how == Close.SERVER_FIRST) {
            in.read();          // wait for the server's FIN
          }
        }
      }
      Thread.sleep(200);
      report("new connection, " + how.name().toLowerCase()
          .replace('_', ' '), t0, port);
    }
  }

  static void report(String name, long t0, int port)
      throws Exception {
    double us = (System.nanoTime() - t0) / 1e3 / N;
    String states = port < 0 ? "" : String.format(
        "   TIME_WAIT %d/%d  CLOSE_WAIT %d/%d  FIN_WAIT2 %d/%d"
            + " (client/server)",
        count("06", port, false), count("06", port, true),
        count("08", port, false), count("08", port, true),
        count("05", port, false), count("05", port, true));
    System.out.printf("%-31s %7.1f µs per request%s%n",
        name, us, states);
  }

  /**
   * Sockets in a state whose local (or remote) port is port.
   * A dual-stack JVM's sockets are listed in tcp6, as
   * ::ffff:127.0.0.1, so read both tables.
   */
  static long count(String state, int port, boolean local)
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
          .filter(f -> f[3].equals(state))
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

  static void oneEach(ServerSocket server, Close how) {
    List<Socket> neverClosed = new ArrayList<>();
    while (!server.isClosed()) {
      try {
        Socket c = server.accept();
        c.setTcpNoDelay(true);
        var in = c.getInputStream();
        c.getOutputStream().write(in.readNBytes(100));
        if (how == Close.SERVER_NEVER) {
          neverClosed.add(c);           // a leak: never closed
          continue;
        }
        if (how != Close.SERVER_FIRST) {
          in.read();            // wait for the client's FIN
        }
        c.close();
      } catch (Exception e) {
        // server closed, or the client reset
      }
    }
  }
}
