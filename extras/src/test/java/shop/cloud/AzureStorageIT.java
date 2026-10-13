package shop.cloud;

import static org.assertj.core.api.Assertions.assertThat;

import com.azure.core.util.BinaryData;
import com.azure.storage.blob.BlobServiceClientBuilder;
import com.azure.storage.queue.QueueClientBuilder;
import org.junit.jupiter.api.Test;
import org.testcontainers.azure.AzuriteContainer;

/** Azurite: Microsoft's open-source Storage emulator. */
class AzureStorageIT {
  static final AzuriteContainer AZURITE =
      new AzuriteContainer(
          "mcr.microsoft.com/azure-storage/azurite:3.37.0");
  static { AZURITE.start(); }

  @Test
  void storesAndReadsAnInvoice() {
    var blobs = new BlobServiceClientBuilder()
        .connectionString(AZURITE.getConnectionString())
        .buildClient();
    var invoices = blobs.createBlobContainer("invoices");
    invoices.getBlobClient("ord-1.txt")
        .upload(BinaryData.fromString("TOTAL 1768.74"));

    String text = invoices.getBlobClient("ord-1.txt")
        .downloadContent().toString();
    assertThat(text).isEqualTo("TOTAL 1768.74");
  }

  @Test
  void queuesAndReceivesAMessage() {
    var queue = new QueueClientBuilder()
        .connectionString(AZURITE.getConnectionString())
        .queueName("orders").buildClient();
    queue.create();
    queue.sendMessage("ord-1 PAID");

    assertThat(queue.receiveMessage().getBody().toString())
        .isEqualTo("ord-1 PAID");
  }
}
