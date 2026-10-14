package deep.tcp;

import java.net.InetSocketAddress;
import java.net.Socket;

/**
 * connect() with no timeout to an address whose packets are
 * dropped: how long until the kernel gives up on its own?
 */
public final class SynRetries {
  public static void main(String[] args) throws Exception {
    long t0 = System.nanoTime();
    try (var s = new Socket()) {
      // no timeout argument: wait as long as the kernel does
      s.connect(new InetSocketAddress("192.0.2.1", 80));
      System.out.println("connected?!");
    } catch (Exception e) {
      System.out.printf("%s after %.1f s%n", e,
          (System.nanoTime() - t0) / 1e9);
    }
  }
}
