from django.db import models
from django.utils.text import slugify
from django.urls import reverse

class Service(models.Model):
    """
    Represents a dynamic, database-driven Service page in the CMS.
    Uses root-level URLs (e.g. /answer-engine-optimization/).
    """
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('PUBLISHED', 'Published'),
    )

    ROBOTS_CHOICES = (
        ('index, follow', 'Index, Follow'),
        ('noindex, nofollow', 'No Index, No Follow'),
        ('index, nofollow', 'Index, Follow'),
        ('noindex, follow', 'No Index, Follow'),
    )

    # Core Fields
    title = models.CharField(max_length=200, help_text="Service title")
    slug = models.CharField(
        max_length=255, 
        unique=True, 
        blank=True, 
        help_text="Custom URL path (e.g. 'answer-engine-optimization' or nested 'india/delhi-ncr/ai-seo-agency-delhi')"
    )
    content = models.TextField(help_text="Service body HTML content")
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='PUBLISHED',
        help_text="Publish status (Draft services are only visible to staff)"
    )

    # Hero / Banner Fields
    hero_heading = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        help_text="Hero Banner Heading (falls back to Service Title if blank)"
    )
    hero_description = models.TextField(
        blank=True, 
        null=True, 
        help_text="Hero Banner Description paragraph (optional)"
    )
    hero_cta_text = models.CharField(
        max_length=100, 
        blank=True, 
        default='Request AI Proposal',
        help_text="Hero Button Text (e.g. 'Request AI Proposal')"
    )
    hero_cta_url = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        help_text="Hero Button Link URL (defaults to /contact/ if blank)"
    )
    hero_banner_image = models.ImageField(
        upload_to='services/banners/',
        blank=True,
        null=True,
        help_text="Custom hero banner background image (optional, falls back to default banner)"
    )

    # SEO Metadata Fields
    meta_title = models.CharField(
        max_length=200, 
        blank=True, 
        null=True, 
        help_text="SEO Meta Title (falls back to Title if blank)"
    )
    meta_description = models.TextField(
        blank=True, 
        null=True, 
        help_text="SEO Meta Description (150-160 characters recommended)"
    )
    meta_keywords = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        help_text="Comma-separated keywords (optional)"
    )
    robots_meta = models.CharField(
        max_length=30, 
        choices=ROBOTS_CHOICES, 
        default='index, follow',
        help_text="Robots indexing instructions"
    )
    canonical_url = models.URLField(
        blank=True, 
        null=True, 
        help_text="Preferred canonical URL (optional, defaults to page URL)"
    )

    # Open Graph Social Sharing Metadata
    og_title = models.CharField(
        max_length=200, 
        blank=True, 
        null=True, 
        help_text="Title shown when shared on social media (optional)"
    )
    og_description = models.TextField(
        blank=True, 
        null=True, 
        help_text="Description shown when shared on social media (optional)"
    )
    og_image = models.ImageField(
        upload_to='services/og/', 
        blank=True, 
        null=True, 
        help_text="Preview image for social sharing (optional)"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Service"
        verbose_name_plural = "Services"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('service_detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Service.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
