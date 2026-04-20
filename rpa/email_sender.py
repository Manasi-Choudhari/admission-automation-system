# rpa/email_sender.py
# Automated email notifications using smtplib
# Configure your SMTP settings in the CONFIG section below

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# ─────────────────────────────────────────────
# EMAIL CONFIGURATION
# Update these settings before using!
# For Gmail: Enable "Less secure app access" OR use App Passwords
# ─────────────────────────────────────────────
EMAIL_CONFIG = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "aissms.ioit.manasi@gmail.com",       # ← Change this
    "sender_password": "omdl ohjc mzoj fmqb",  # ← Change this (Gmail App Password)
    "sender_name": "Admissions Office",
    "institution_name": "Bright Future University"
}


def send_email(to_email: str, subject: str, html_body: str) -> bool:
    """
    Core email sending function using smtplib with TLS.
    Returns True if sent successfully, False otherwise.
    """
    try:
        # Create MIME message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{EMAIL_CONFIG['sender_name']} <{EMAIL_CONFIG['sender_email']}>"
        message["To"] = to_email

        # Attach HTML body
        html_part = MIMEText(html_body, "html")
        message.attach(html_part)

        # Create SSL context for secure connection
        context = ssl.create_default_context()

        # Connect and send
        with smtplib.SMTP(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"]) as server:
            server.ehlo()
            server.starttls(context=context)   # Start TLS encryption
            server.login(EMAIL_CONFIG["sender_email"], EMAIL_CONFIG["sender_password"])
            server.sendmail(
                EMAIL_CONFIG["sender_email"],
                to_email,
                message.as_string()
            )

        print(f"[EmailSender] ✅ Email sent to {to_email}: {subject}")
        return True

    except smtplib.SMTPAuthenticationError:
        print(f"[EmailSender] ❌ Authentication failed. Check email/password in EMAIL_CONFIG.")
        return False
    except smtplib.SMTPException as e:
        print(f"[EmailSender] ❌ SMTP error: {e}")
        return False
    except Exception as e:
        print(f"[EmailSender] ❌ Unexpected error: {e}")
        return False


# ─────────────────────────────────────────────
# EMAIL TEMPLATES
# ─────────────────────────────────────────────

def build_base_template(title: str, content: str, color: str = "#2563eb") -> str:
    """Wraps content in a clean, responsive HTML email template."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
    </head>
    <body style="margin:0;padding:0;background:#f0f4f8;font-family:Georgia,serif;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#f0f4f8;padding:40px 20px;">
            <tr><td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
                    <!-- Header -->
                    <tr>
                        <td style="background:{color};padding:32px 40px;text-align:center;">
                            <h1 style="color:#fff;margin:0;font-size:24px;letter-spacing:1px;">
                                🎓 {EMAIL_CONFIG['institution_name']}
                            </h1>
                            <p style="color:rgba(255,255,255,0.85);margin:8px 0 0;font-size:14px;">
                                Admissions Office
                            </p>
                        </td>
                    </tr>
                    <!-- Body -->
                    <tr>
                        <td style="padding:40px;">
                            {content}
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="background:#f8fafc;padding:24px 40px;text-align:center;border-top:1px solid #e2e8f0;">
                            <p style="color:#94a3b8;font-size:12px;margin:0;">
                                This is an automated message from {EMAIL_CONFIG['institution_name']} Admissions System.<br>
                                Please do not reply to this email. Contact admissions@university.edu for help.
                            </p>
                            <p style="color:#cbd5e1;font-size:11px;margin:8px 0 0;">
                                © {datetime.now().year} {EMAIL_CONFIG['institution_name']}
                            </p>
                        </td>
                    </tr>
                </table>
            </td></tr>
        </table>
    </body>
    </html>
    """


def send_application_received(to_email: str, student_name: str, app_id: int, course: str) -> bool:
    """
    Email 1: Sent when a student submits an application.
    Confirms receipt and provides the application ID.
    """
    subject = f"✅ Application Received — Ref #{app_id} | {EMAIL_CONFIG['institution_name']}"

    content = f"""
        <h2 style="color:#1e293b;margin:0 0 16px;">Application Received!</h2>
        <p style="color:#475569;line-height:1.7;">Dear <strong>{student_name}</strong>,</p>
        <p style="color:#475569;line-height:1.7;">
            Thank you for applying to <strong>{EMAIL_CONFIG['institution_name']}</strong>. 
            We have successfully received your application for the following program:
        </p>
        
        <!-- Info Box -->
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#eff6ff;border-radius:8px;margin:24px 0;">
            <tr>
                <td style="padding:24px;">
                    <table width="100%" cellpadding="8" cellspacing="0">
                        <tr>
                            <td style="color:#64748b;font-size:13px;width:40%;">📋 Application ID</td>
                            <td style="color:#1e293b;font-weight:bold;font-size:16px;">#{app_id}</td>
                        </tr>
                        <tr>
                            <td style="color:#64748b;font-size:13px;">🎓 Program Applied</td>
                            <td style="color:#1e293b;font-weight:bold;">{course}</td>
                        </tr>
                        <tr>
                            <td style="color:#64748b;font-size:13px;">📅 Date Received</td>
                            <td style="color:#1e293b;">{datetime.now().strftime('%B %d, %Y')}</td>
                        </tr>
                        <tr>
                            <td style="color:#64748b;font-size:13px;">⏳ Status</td>
                            <td style="color:#f59e0b;font-weight:bold;">Under Review</td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
        
        <p style="color:#475569;line-height:1.7;">
            Our admissions team will review your documents carefully. 
            You can track your application status anytime using your Application ID above.
        </p>
        <p style="color:#475569;line-height:1.7;">
            The review process typically takes <strong>5–7 business days</strong>. 
            You will receive another email once a decision has been made.
        </p>
        <p style="color:#475569;line-height:1.7;margin-top:24px;">
            Best regards,<br>
            <strong>The Admissions Team</strong><br>
            {EMAIL_CONFIG['institution_name']}
        </p>
    """

    return send_email(to_email, subject, build_base_template("Application Received", content, "#2563eb"))


def send_approval_email(to_email: str, student_name: str, app_id: int, course: str) -> bool:
    """
    Email 2: Sent when admin approves an application.
    Celebrates the acceptance and provides next steps.
    """
    subject = f"🎉 Congratulations! You're Admitted — {course} | {EMAIL_CONFIG['institution_name']}"

    content = f"""
        <div style="text-align:center;margin-bottom:32px;">
            <div style="font-size:64px;">🎉</div>
            <h2 style="color:#16a34a;margin:8px 0;">Congratulations, {student_name}!</h2>
            <p style="color:#64748b;font-size:15px;">Your application has been approved!</p>
        </div>
        
        <p style="color:#475569;line-height:1.7;">
            We are thrilled to inform you that your application to <strong>{EMAIL_CONFIG['institution_name']}</strong> 
            has been <span style="color:#16a34a;font-weight:bold;">APPROVED</span>!
        </p>
        
        <!-- Approval Box -->
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#f0fdf4;border:2px solid #86efac;border-radius:8px;margin:24px 0;">
            <tr>
                <td style="padding:24px;">
                    <table width="100%" cellpadding="8" cellspacing="0">
                        <tr>
                            <td style="color:#64748b;font-size:13px;width:40%;">📋 Application ID</td>
                            <td style="color:#1e293b;font-weight:bold;">#{app_id}</td>
                        </tr>
                        <tr>
                            <td style="color:#64748b;font-size:13px;">🎓 Admitted Program</td>
                            <td style="color:#1e293b;font-weight:bold;">{course}</td>
                        </tr>
                        <tr>
                            <td style="color:#64748b;font-size:13px;">✅ Decision</td>
                            <td style="color:#16a34a;font-weight:bold;font-size:16px;">APPROVED</td>
                        </tr>
                        <tr>
                            <td style="color:#64748b;font-size:13px;">📅 Decision Date</td>
                            <td style="color:#1e293b;">{datetime.now().strftime('%B %d, %Y')}</td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
        
        <h3 style="color:#1e293b;">📌 Next Steps:</h3>
        <ol style="color:#475569;line-height:2;">
            <li>Log in to your student portal to complete enrollment</li>
            <li>Submit the enrollment fee payment by the deadline</li>
            <li>Complete the online orientation program</li>
            <li>Pick up your student ID from the registrar's office</li>
        </ol>
        
        <p style="color:#475569;line-height:1.7;margin-top:24px;">
            Welcome to the <strong>{EMAIL_CONFIG['institution_name']}</strong> family! 
            We look forward to seeing you succeed.
        </p>
        <p style="color:#475569;line-height:1.7;">
            Warm regards,<br>
            <strong>The Admissions Team</strong><br>
            {EMAIL_CONFIG['institution_name']}
        </p>
    """

    return send_email(to_email, subject, build_base_template("Application Approved", content, "#16a34a"))


def send_rejection_email(to_email: str, student_name: str, app_id: int, course: str, reason: str = "") -> bool:
    """
    Email 3: Sent when admin rejects an application.
    Politely informs the student with the reason if provided.
    """
    subject = f"Application Update — Ref #{app_id} | {EMAIL_CONFIG['institution_name']}"

    reason_section = ""
    if reason:
        reason_section = f"""
        <div style="background:#fef2f2;border:1px solid #fca5a5;border-radius:8px;padding:16px;margin:16px 0;">
            <p style="color:#991b1b;font-weight:bold;margin:0 0 4px;">Feedback from Admissions Committee:</p>
            <p style="color:#7f1d1d;margin:0;">{reason}</p>
        </div>
        """

    content = f"""
        <h2 style="color:#1e293b;margin:0 0 16px;">Application Status Update</h2>
        <p style="color:#475569;line-height:1.7;">Dear <strong>{student_name}</strong>,</p>
        <p style="color:#475569;line-height:1.7;">
            Thank you for your interest in <strong>{EMAIL_CONFIG['institution_name']}</strong> 
            and for the time you invested in your application for <strong>{course}</strong>.
        </p>
        <p style="color:#475569;line-height:1.7;">
            After careful consideration by our admissions committee, we regret to inform you 
            that your application (Ref: #{app_id}) was <span style="color:#dc2626;font-weight:bold;">not successful</span> 
            for this admission cycle.
        </p>
        
        {reason_section}
        
        <p style="color:#475569;line-height:1.7;">
            We understand this is disappointing news. Please know that this decision was made 
            after thorough review and does not diminish your potential or worth as a student.
        </p>
        
        <div style="background:#f8fafc;border-radius:8px;padding:20px;margin:20px 0;">
            <h3 style="color:#1e293b;margin:0 0 12px;">💡 What You Can Do Next:</h3>
            <ul style="color:#475569;line-height:2;margin:0;padding-left:20px;">
                <li>Consider applying for the next admission cycle</li>
                <li>Strengthen your academic credentials</li>
                <li>Explore other programs that may be a good fit</li>
                <li>Contact our counseling office for guidance</li>
            </ul>
        </div>
        
        <p style="color:#475569;line-height:1.7;">
            We encourage you not to give up and wish you all the best in your educational journey.
        </p>
        <p style="color:#475569;line-height:1.7;margin-top:24px;">
            Sincerely,<br>
            <strong>The Admissions Committee</strong><br>
            {EMAIL_CONFIG['institution_name']}
        </p>
    """

    return send_email(to_email, subject, build_base_template("Application Update", content, "#dc2626"))



def send_documents_required_email(
    to_email: str,
    student_name: str,
    app_id: int,
    course: str,
    missing_docs: list,
    issues: list = None
) -> bool:
    """
    Email 4 (NEW — RPA): Sent automatically when the RPA pipeline detects
    that required caste/income documents are missing or invalid.
    Lists exactly what the student needs to provide.
    """
    issues = issues or []
    subject = f"⚠️ Action Required: Documents Missing — Ref #{app_id} | {EMAIL_CONFIG['institution_name']}"

    # Build missing docs list HTML
    missing_items = "".join(
        f"<li style='padding:6px 0;color:#92400e;'>"
        f"<strong>📄 {doc}</strong></li>"
        for doc in missing_docs
    )

    # Build issues list HTML
    issues_section = ""
    if issues:
        issues_html = "".join(
            f"<li style='padding:4px 0;color:#7f1d1d;font-size:13px;'>{iss}</li>"
            for iss in issues
        )
        issues_section = f"""
        <div style="background:#fef2f2;border:1px solid #fca5a5;border-radius:8px;padding:16px;margin:16px 0;">
            <p style="color:#991b1b;font-weight:bold;margin:0 0 8px;">Details from our automated checker:</p>
            <ul style="margin:0;padding-left:20px;">{issues_html}</ul>
        </div>
        """

    content = f"""
        <h2 style="color:#92400e;margin:0 0 16px;">⚠️ Documents Required</h2>
        <p style="color:#475569;line-height:1.7;">Dear <strong>{student_name}</strong>,</p>
        <p style="color:#475569;line-height:1.7;">
            Thank you for submitting your application (Ref: <strong>#{app_id}</strong>) for
            <strong>{course}</strong> at <strong>{EMAIL_CONFIG['institution_name']}</strong>.
        </p>
        <p style="color:#475569;line-height:1.7;">
            Our automated document verification system has reviewed your submission and found that
            the following <strong>required documents are missing or could not be verified</strong>:
        </p>

        <!-- Missing documents box -->
        <table width="100%" cellpadding="0" cellspacing="0"
               style="background:#fffbeb;border:2px solid #fcd34d;border-radius:8px;margin:20px 0;">
            <tr><td style="padding:20px;">
                <p style="color:#92400e;font-weight:bold;margin:0 0 12px;">📋 Missing / Unverified Documents:</p>
                <ul style="margin:0;padding-left:20px;">{missing_items}</ul>
            </td></tr>
        </table>

        {issues_section}

        <h3 style="color:#1e293b;">📌 What You Need to Do:</h3>
        <ol style="color:#475569;line-height:2;">
            <li>Log in to the admissions portal</li>
            <li>Navigate to <em>My Application</em> and withdraw/resubmit with the correct documents</li>
            <li>Ensure all certificates are issued by the <strong>competent government authority</strong></li>
            <li>Documents must clearly show your name, category, and issuing authority's seal/signature</li>
        </ol>

        <div style="background:#f0fdf4;border:1px solid #86efac;border-radius:8px;padding:16px;margin:20px 0;">
            <p style="color:#166534;font-weight:bold;margin:0 0 4px;">💡 Tip</p>
            <p style="color:#166534;margin:0;">
                Make sure your caste/income certificate is issued within the last <strong>3 years</strong>
                and is from a Tehsildar, SDO, or District Magistrate of your home district.
            </p>
        </div>

        <p style="color:#475569;line-height:1.7;">
            If you believe this is an error or need assistance, please contact our admissions office
            at <a href="mailto:admissions@university.edu">admissions@university.edu</a>.
        </p>
        <p style="color:#475569;line-height:1.7;margin-top:24px;">
            Regards,<br>
            <strong>Automated Admissions System</strong><br>
            {EMAIL_CONFIG['institution_name']}
        </p>
    """

    return send_email(to_email, subject, build_base_template("Documents Required", content, "#d97706"))


# ─────────────────────────────────────────────
# Standalone test (run directly to test email config)
# ─────────────────────────────────────────────
if __name__ == "__main__":
    TEST_EMAIL = "test@example.com"   # ← Change to your test email

    print("=== Email Sender Test ===")
    print("Testing application received email...")
    send_application_received(TEST_EMAIL, "Test Student", 12345, "Computer Science")

    print("\nTesting approval email...")
    send_approval_email(TEST_EMAIL, "Test Student", 12345, "Computer Science")

    print("\nTesting rejection email...")
    send_rejection_email(TEST_EMAIL, "Test Student", 12345, "Computer Science", "Incomplete documents submitted.")

    print("\nTesting documents required email...")
    send_documents_required_email(
        TEST_EMAIL, "Test Student", 12345, "Computer Science",
        missing_docs=["Caste Certificate", "Income / Non-Creamy Layer Certificate"],
        issues=["Caste certificate does not contain expected keywords."]
    )

