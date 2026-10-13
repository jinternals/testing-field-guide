package shop.http;

/** The price service failed in a way worth retrying. */
public class UpstreamException extends RuntimeException {
  public UpstreamException(String message, Throwable cause) {
    super(message, cause);
  }
}
