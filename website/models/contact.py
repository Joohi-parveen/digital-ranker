from django.db import models

class ContactMessage(models.Model):
    """
    Model to store contact/inquiry messages from visitors.
    """
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        unpack_ipv4=False,
        verbose_name="IP Address",
        help_text="Visitor IP address captured upon submission."
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Contact Message"
        verbose_name_plural = "Contact Messages"

    def __str__(self):
        return f"{self.name} - {self.subject}"
