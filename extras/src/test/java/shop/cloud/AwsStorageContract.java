package shop.cloud;

import static org.assertj.core.api.Assertions.assertThat;

import java.net.URI;
import org.junit.jupiter.api.Test;
import software.amazon.awssdk.auth.credentials.*;
import software.amazon.awssdk.core.sync.RequestBody;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.sqs.SqsClient;
import software.amazon.awssdk.services.sqs.model.Message;

/** The same S3 + SQS tests, run against any AWS emulator. */
abstract class AwsStorageContract {
  abstract URI endpoint();

  static final StaticCredentialsProvider TEST_KEYS =
      StaticCredentialsProvider.create(
          AwsBasicCredentials.create("test", "test"));

  S3Client s3() {
    return S3Client.builder().endpointOverride(endpoint())
        .region(Region.US_EAST_1)
        .credentialsProvider(TEST_KEYS)
        .forcePathStyle(true).build();
  }

  SqsClient sqs() {
    return SqsClient.builder().endpointOverride(endpoint())
        .region(Region.US_EAST_1)
        .credentialsProvider(TEST_KEYS).build();
  }

  @Test
  void storesAndReadsAnInvoice() {
    try (var s3 = s3()) {
      s3.createBucket(b -> b.bucket("invoices"));
      s3.putObject(b -> b.bucket("invoices").key("ord-1.txt"),
          RequestBody.fromString("TOTAL 1768.74"));

      String text = s3.getObjectAsBytes(b -> b
          .bucket("invoices").key("ord-1.txt")).asUtf8String();
      assertThat(text).isEqualTo("TOTAL 1768.74");
    }
  }

  @Test
  void queuesAndReceivesAMessage() {
    try (var sqs = sqs()) {
      String url = sqs.createQueue(b -> b.queueName("orders"))
          .queueUrl();
      sqs.sendMessage(b -> b.queueUrl(url)
          .messageBody("ord-1 PAID"));

      var messages = sqs.receiveMessage(
          b -> b.queueUrl(url).waitTimeSeconds(5)).messages();
      assertThat(messages).extracting(Message::body)
          .containsExactly("ord-1 PAID");
    }
  }
}
