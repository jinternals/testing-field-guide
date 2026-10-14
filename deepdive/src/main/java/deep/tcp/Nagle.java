package deep.tcp;

import deep.Stats;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.InetAddress;
import java.net.ServerSocket;
import java.net.Socket;

/**
 * One request/response on one connection, 200 times. A request
 * is 100 bytes, a response 100 bytes; each is written in one or
 * two write() calls, with or without TCP_NODELAY.
 */
public final class Nagle {
  static final int ROUNDS = 200;

  record Setup(String name, int clientWrites, boolean clientNoDelay,
      int serverWrites, boolean serverNoDelay) {}

  public static void main(String[] args) throws Exception {
    if (args.length > 0 && args[0].equals("trace")) {
      run(new Setup("trace", 2, false, 1, false), 18080, 3);
      return;
    }
    Setup[] setups = {
        new Setup("client 2 writes, Nagle on", 2, false, 1, false),
        new Setup("client 2 writes, TCP_NODELAY", 2, true, 1, false),
        new Setup("client 1 write,  Nagle on", 1, false, 1, false),
        new Setup("server 2 writes, Nagle on", 1, false, 2, false),
        new Setup("server 2 writes, TCP_NODELAY", 1, false, 2, true)};
    for (Setup s : setups) {
      long[] rtt = run(s, 0, ROUNDS);
      Stats st = new Stats(rtt);
      System.out.printf("%-30s %s  over 30 ms: %d of %d%n",
          s.name(), st.line(), st.countAbove(30), ROUNDS);
    }
  }

  static long[] run(Setup s, int port, int rounds) throws Exception {
    var lo = InetAddress.getLoopbackAddress();
    try (var server = new ServerSocket(port, 50, lo)) {
      Thread.ofPlatform().daemon().start(() -> serve(server, s));
      try (var socket = new Socket(lo, server.getLocalPort())) {
        socket.setTcpNoDelay(s.clientNoDelay());
        return exchange(socket, s.clientWrites(), rounds);
      }
    }
  }

  static long[] exchange(Socket socket, int writes, int rounds)
      throws Exception {
    OutputStream out = socket.getOutputStream();
    InputStream in = socket.getInputStream();
    long[] rtt = new long[rounds];
    for (int i = 0; i < rounds; i++) {
      long t0 = System.nanoTime();
      write(out, writes);
      in.readNBytes(100);
      rtt[i] = System.nanoTime() - t0;
    }
    return rtt;
  }

  static void serve(ServerSocket server, Setup s) {
    try (Socket c = server.accept()) {
      c.setTcpNoDelay(s.serverNoDelay());
      InputStream in = c.getInputStream();
      OutputStream out = c.getOutputStream();
      while (in.readNBytes(100).length == 100) {
        write(out, s.serverWrites());
      }
    } catch (Exception e) {
      // client closed
    }
  }

  /** 100 bytes in one write, or 50 + 50 like headers + body. */
  static void write(OutputStream out, int writes) throws Exception {
    if (writes == 1) {
      out.write(new byte[100]);
    } else {
      out.write(new byte[50]);
      out.write(new byte[50]);
    }
    out.flush();
  }
}
