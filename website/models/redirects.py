from django.db import models


class UrlRedirect(models.Model):
    """
    Manages 301 Permanent Redirects for CMS pages whose URLs/slugs have changed.
    Ensures indexed Google search rankings and backlink authority are preserved.
    """
    old_path = models.CharField(
        max_length=255, 
        unique=True, 
        db_index=True, 
        help_text="Original URL path that is being redirected (without leading/trailing slashes)"
    )
    new_path = models.CharField(
        max_length=255, 
        help_text="Target URL path to redirect to (without leading/trailing slashes)"
    )
    http_status = models.PositiveSmallIntegerField(
        default=301,
        help_text="HTTP status code for the redirect (default 301 Permanent)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = "URL Redirect"
        verbose_name_plural = "URL Redirects"

    def __str__(self):
        return f"/{self.old_path}/ -> /{self.new_path}/ ({self.http_status})"

    def clean(self):
        super().clean()
        if self.old_path:
            self.old_path = self.old_path.strip().strip('/')
        if self.new_path:
            self.new_path = self.new_path.strip().strip('/')

