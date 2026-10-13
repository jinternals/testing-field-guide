package shop.mail;

import jakarta.mail.*;
import jakarta.mail.internet.*;
import java.util.Properties;

/** Sends order e-mails through any SMTP server. */
public class OrderMailer {
  private final Session session;

  public OrderMailer(String host, int port) {
    Properties props = new Properties();
    props.put("mail.smtp.host", host);
    props.put("mail.smtp.port", String.valueOf(port));
    props.put("mail.smtp.connectiontimeout", "2000");
    session = Session.getInstance(props);
  }

  public void sendConfirmation(String to, String orderId,
      String total) throws MessagingException {
    var message = new MimeMessage(session);
    message.setFrom(new InternetAddress("orders@shop.example"));
    message.setRecipients(Message.RecipientType.TO, to);
    message.setSubject("Order " + orderId + " confirmed", "UTF-8");
    message.setText("Thank you! Total: " + total, "UTF-8");
    Transport.send(message);
  }
}
