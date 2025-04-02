import { MailerSend, EmailParams, Sender, Recipient } from "mailersend";

const MAILERSEND_API_KEY = "mlsn.d6a5ea105e3ecc8e2923f2e6a4370fdceb3051fea80e3a117854967ce955163a";

const mailerSend = new MailerSend({
  apiKey: MAILERSEND_API_KEY,
});

export interface EmailOptions {
  to: string;
  subject: string;
  html: string;
  text?: string;
  from?: string;
  fromName?: string;
}

export async function sendEmail({
  to,
  subject,
  html,
  text,
  from = "noreply@yourdomain.com",
  fromName = "InsightFlow"
}: EmailOptions) {
  try {
    const sentFrom = new Sender(from, fromName);
    const recipients = [new Recipient(to)];

    const emailParams = new EmailParams()
      .setFrom(sentFrom)
      .setTo(recipients)
      .setSubject(subject)
      .setHtml(html);

    if (text) {
      emailParams.setText(text);
    }

    const response = await mailerSend.email.send(emailParams);
    return response;
  } catch (error) {
    console.error('Error sending email:', error);
    throw error;
  }
} 