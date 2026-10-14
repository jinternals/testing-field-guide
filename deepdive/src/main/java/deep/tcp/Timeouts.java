package deep.tcp;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.InetAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse.BodyHandlers;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;

/**
 * What each timeout actually bounds, against three bad peers:
 * a server that never answers, one that sends its body a byte
 * every 0.5 s, and an address whose packets are dropped
 * (192.0.2.1, RFC 5737; CI drops it with iptables), so the
 * TCP handshake never completes.
 */
public final class Timeouts {
  static final InetAddress LO = InetAddress.getLoopbackAddress();
  static final long GIVE_UP_S = 5;

  public static void main(String[] args) throws Exception {
    int silent = silentServer();
    int trickle = trickleServer();
    Duration none = null;
    Duration s1 = Duration.ofSeconds(1);
    Duration s2 = Duration.ofSeconds(2);
    call("silent  | no timeouts", silent, none, none);
    call("silent  | connectTimeout 1 s", silent, s1, none);
    call("silent  | request timeout 2 s", silent, none, s2);
    call("trickle | request timeout 2 s", trickle, none, s2);
    call("dropped | no timeouts", DROPPED, none, none);
    call("dropped | request timeout 2 s", DROPPED, none, s2);
    call("dropped | connectTimeout 1 s", DROPPED, s1, none);
    rawRead("trickle | Socket soTimeout 1 s", trickle);
  }

  static final String DROPPED = "192.0.2.1:80";

  static void call(String name, int port, Duration connect,
      Duration request) throws Exception {
    call(name, "127.0.0.1:" + port, connect, request);
  }

  static void call(String name, String hostPort, Duration connect,
      Duration request) throws Exception {
    var client = HttpClient.newBuilder();
    if (connect != null) {
      client.connectTimeout(connect);
    }
    var req = HttpRequest.newBuilder(
        URI.create("http://" + hostPort + "/"));
    if (request != null) {
      req.timeout(request);
    }
    long t0 = System.nanoTime();
    String result;
    try {
      var r = client.build().sendAsync(req.build(),
          BodyHandlers.ofString()).get(GIVE_UP_S, TimeUnit.SECONDS);
      result = "returned " + r.statusCode() + ", body "
          + r.body().length() + " bytes";
    } catch (TimeoutException e) {
      result = "still waiting after " + GIVE_UP_S + " s";
    } catch (Exception e) {
      result = e.getCause().getClass().getSimpleName();
    }
    print(name, t0, result);
  }

  /** java.net.Socket: the timeout applies to each read(). */
  static void rawRead(String name, int port) throws Exception {
    long t0 = System.nanoTime();
    try (var s = new Socket(LO, port)) {
      s.setSoTimeout(1000);
      s.getOutputStream().write("GET / HTTP/1.1\r\n\r\n".getBytes());
      byte[] all = s.getInputStream().readAllBytes();
      print(name, t0, "returned " + all.length + " bytes, no error");
    }
  }

  static void print(String name, long t0, String result) {
    System.out.printf("%-34s %5.1f s  %s%n", name,
        (System.nanoTime() - t0) / 1e9, result);
  }

  /** Accepts and reads the request, never answers. */
  static int silentServer() throws Exception {
    var server = new ServerSocket(0, 50, LO);
    Thread.ofPlatform().daemon().start(() -> {
      List<Socket> keep = new ArrayList<>();
      while (true) {
        try {
          keep.add(server.accept());
        } catch (Exception e) {
          return;
        }
      }
    });
    return server.getLocalPort();
  }

  /** Headers at once, then 12 body bytes, one every 0.5 s. */
  static int trickleServer() throws Exception {
    var server = new ServerSocket(0, 50, LO);
    Thread.ofPlatform().daemon().start(() -> {
      while (true) {
        try {
          Socket c = server.accept();
          Thread.ofPlatform().daemon().start(() -> trickle(c));
        } catch (Exception e) {
          return;
        }
      }
    });
    return server.getLocalPort();
  }

  static void trickle(Socket c) {
    try (c) {
      var in = new BufferedReader(
          new InputStreamReader(c.getInputStream()));
      while (!in.readLine().isEmpty()) {
        // skip the request line and headers
      }
      var out = c.getOutputStream();
      out.write(("HTTP/1.1 200 OK\r\nContent-Length: 12\r\n"
          + "Connection: close\r\n\r\n").getBytes());
      out.flush();
      for (int i = 0; i < 12; i++) {
        Thread.sleep(500);
        out.write('x');
        out.flush();
      }
    } catch (Exception e) {
      // client gave up
    }
  }
}
