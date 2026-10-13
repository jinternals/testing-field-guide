package shop.cache;

import java.io.Serializable;

/** Cached with the default JDK serializer: Serializable. */
public record Price(String sku, long paise)
    implements Serializable {}
