package shop.jobs;

import java.time.Instant;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import org.springframework.stereotype.Component;

/** Carts and when each was last touched. */
@Component
public class CartStore {
  private final Map<String, Instant> touched =
      new ConcurrentHashMap<>();

  public void touch(String cartId, Instant at) {
    touched.put(cartId, at);
  }

  public int removeTouchedBefore(Instant cutoff) {
    int before = touched.size();
    touched.values().removeIf(at -> at.isBefore(cutoff));
    return before - touched.size();
  }

  public Set<String> ids() {
    return Set.copyOf(touched.keySet());
  }
}
