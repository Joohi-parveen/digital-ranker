from django.db import models

class PageSEOSetting(models.Model):
    """
    Stores page-specific SEO configurations and settings.
    """
    PAGE_CHOICES = (
        ('home', 'Home'),
        ('about', 'About'),
        ('services', 'Services'),
        ('blog', 'Blog'),
        ('contact', 'Contact'),
        ('team', 'Team'),
    )

    ROBOTS_CHOICES = (
        ('index, follow', 'Index, Follow'),
        ('noindex, nofollow', 'No Index, No Follow'),
        ('index, nofollow', 'Index, No Follow'),
        ('noindex, follow', 'No Index, Follow'),
    )

    page_name = models.CharField(
        max_length=100,
        unique=True,
        help_text="The page this SEO configuration belongs to."
    )
    site_title = models.CharField(
        max_length=100,
        default="AI Digital Ranker",
        help_text="Standard prefix or site name (e.g. My Website)."
    )
    meta_title = models.CharField(
        max_length=150,
        help_text="Page title displayed in search engines and tab bar."
    )
    meta_description = models.TextField(
        help_text="Summary description of the page (150-160 characters suggested)."
    )
    meta_keywords = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Comma-separated keywords (optional)."
    )
    canonical_url = models.URLField(
        blank=True,
        null=True,
        help_text="Preferred canonical URL (optional)."
    )
    robots_meta = models.CharField(
        max_length=30,
        choices=ROBOTS_CHOICES,
        default='index, follow',
        help_text="Robots indexing instructions."
    )
    og_title = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        help_text="Title shown when shared on social media (optional)."
    )
    og_description = models.TextField(
        blank=True,
        null=True,
        help_text="Description shown when shared on social media (optional)."
    )
    og_image = models.ImageField(
        upload_to='seo/og/',
        blank=True,
        null=True,
        help_text="Preview image for social sharing (optional)."
    )
    favicon = models.ImageField(
        upload_to='seo/favicons/',
        blank=True,
        null=True,
        help_text="Favicon shortcut icon (optional)."
    )

    class Meta:
        verbose_name = "Page SEO Setting"
        verbose_name_plural = "Page SEO Settings"

    def __str__(self):
        return f"{self.get_page_name_display()} Page SEO Settings"


# Cache invalidation signals
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache

@receiver([post_save, post_delete], sender=PageSEOSetting)
def clear_seo_settings_cache(sender, instance, **kwargs):
    """
    Clears cached PageSEOSetting variables when updated or deleted.
    """
    cache.delete(f"seo_settings_{instance.page_name}")
    # Also clear the fallback home cache key in case other pages were using it
    cache.delete("seo_settings_home")

