package shop.flags;

import org.springframework.boot.context.properties.ConfigurationProperties;

/** Feature flags, e.g. shop.features.bulk-discount=true */
@ConfigurationProperties("shop.features")
public record Features(boolean bulkDiscount) {}
