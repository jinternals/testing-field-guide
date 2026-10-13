package shop.mail;

import static org.assertj.core.api.Assertions.*;

import com.icegreen.greenmail.junit5.GreenMailExtension;
import com.icegreen.greenmail.util.ServerSetupTest;
import jakarta.mail.MessagingException;
import jakarta.mail.internet.MimeMessage;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.RegisterExtension;

/** GreenMail: a real SMTP server inside the test JVM. */
class OrderMailerTest {
  @RegisterExtension                  // fresh mailbox per test
  static GreenMailExtension smtp = new GreenMailExtension(
      ServerSetupTest.SMTP.dynamicPort());   // free port: no clashes

  OrderMailer mailer() {
    int port = smtp.getSmtp().getPort();
    return new OrderMailer("localhost", port);
  }

  @Test
  void confirmationIsSentToTheCustomer() throws Exception {
    mailer().sendConfirmation("asha@example.com", "ord-1",
        "₹1,140.00");

    assertThat(smtp.waitForIncomingEmail(2_000, 1)).isTrue();
    MimeMessage mail = smtp.getReceivedMessages()[0];
    assertThat(mail.getSubject())
        .isEqualTo("Order ord-1 confirmed");
    assertThat(mail.getAllRecipients())
        .extracting(Object::toString)
        .containsExactly("asha@example.com");
    assertThat((String) mail.getContent())
        .isEqualTo("Thank you! Total: ₹1,140.00");
  }

  @Test
  void smtpServerDownIsAnError() {
    var nobodyListening = new OrderMailer("localhost", 1);

    assertThatThrownBy(() -> nobodyListening.sendConfirmation(
            "asha@example.com", "ord-2", "₹10.00"))
        .isInstanceOf(MessagingException.class);
  }
}
