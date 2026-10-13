package shop.cache;

/** Forgot "implements Serializable": caching it fails. */
public record Quote(String sku, long paise) {}
