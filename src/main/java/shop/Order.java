package shop;

import java.time.Instant;
import java.util.List;

public record Order(String id, String customerEmail, List<Item> items,
          Money total, Instant placedAt) {}
