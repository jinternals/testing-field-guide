package shop.cache;

/** Forgot "implements Serializable": caching it fails at runtime. */
public record Quote(String sku, long paise) {}
