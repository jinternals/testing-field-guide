package shop.cache;

import java.io.Serializable;

/** Cached in Redis with the default JDK serializer: must be Serializable. */
public record Price(String sku, long paise) implements Serializable {}
