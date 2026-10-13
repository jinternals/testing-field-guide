package shop.cloud;

import java.net.URI;
import org.testcontainers.containers.GenericContainer;

/** Moto: open-source AWS emulator (Apache-2.0); no account. */
class MotoAwsIT extends AwsStorageContract {
  static final GenericContainer<?> MOTO =
      new GenericContainer<>("motoserver/moto:5.2.4")
          .withExposedPorts(5000);
  static { MOTO.start(); }

  @Override URI endpoint() {
    return URI.create("http://" + MOTO.getHost() + ":"
        + MOTO.getMappedPort(5000));
  }
}
