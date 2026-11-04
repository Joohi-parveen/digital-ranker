import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def send_lead_emails(lead):
    """
    Sends two emails upon receiving a lead:
    1. Team notification to NOTIFICATION_EMAILS (sales@aidigitalranker.com & saddam@matebiz.com)
       with Reply-To header pointing to lead.email.
    2. Auto-responder thank you email sent to the visitor (lead.email).
    
    Safe execution: errors are logged without interrupting the visitor's UX.
    """
    context = {"lead": lead}
    
    # --------------------------------------------------------------------------
    # 1. Admin/Sales Team Notification
    # --------------------------------------------------------------------------
    try:
        admin_recipients = getattr(settings, 'NOTIFICATION_EMAILS', ['sales@aidigitalranker.com', 'saddam@matebiz.com'])
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'AI Digital Ranker <sales@aidigitalranker.com>')
        
        subject_line = f"New Inquiry: {lead.name} - {lead.subject or 'General Inquiry'}"
        text_content = render_to_string("website/emails/admin_new_lead.txt", context)
        html_content = render_to_string("website/emails/admin_new_lead.html", context)
        
        # Build email with Reply-To set to the visitor so when team clicks 'Reply', it replies to lead
        reply_to_list = [lead.email] if lead.email else []
        
        admin_email = EmailMultiAlternatives(
            subject=subject_line,
            body=text_content,
            from_email=from_email,
            to=admin_recipients,
            reply_to=reply_to_list
        )
        admin_email.attach_alternative(html_content, "text/html")
        admin_email.send(fail_silently=False)
        logger.info(f"Admin notification email sent successfully for lead #{lead.id} ({lead.email}) to {admin_recipients}")
    except Exception as e:
        logger.error(f"Failed to send admin notification email for lead #{lead.id}: {e}", exc_info=True)

    # --------------------------------------------------------------------------
    # 2. Visitor Auto-Responder Acknowledgment Email
    # --------------------------------------------------------------------------
    if lead.email:
        try:
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'AI Digital Ranker <sales@aidigitalranker.com>')
            user_subject = "Thank you for contacting AI Digital Ranker - We received your inquiry"
            user_text = render_to_string("website/emails/user_acknowledgement.txt", context)
            user_html = render_to_string("website/emails/user_acknowledgement.html", context)
            
            user_email = EmailMultiAlternatives(
                subject=user_subject,
                body=user_text,
                from_email=from_email,
                to=[lead.email],
                reply_to=['sales@aidigitalranker.com']
            )
            user_email.attach_alternative(user_html, "text/html")
            user_email.send(fail_silently=False)
            logger.info(f"Auto-responder email sent successfully to visitor {lead.email} for lead #{lead.id}")
        except Exception as e:
            logger.error(f"Failed to send auto-responder email to visitor {lead.email} for lead #{lead.id}: {e}", exc_info=True)
