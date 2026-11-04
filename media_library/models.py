import os
from django.db import models
from PIL import Image

class MediaAsset(models.Model):
    """
    Represents an uploaded media asset (image/SVG) in the CMS Media Library.
    Stores metadata like file size and dimensions (for raster formats).
    """
    original_filename = models.CharField(
        max_length=255,
        help_text="The original name of the uploaded file."
    )
    file = models.FileField(
        upload_to='uploads/',
        help_text="The uploaded media file."
    )
    alt_text = models.CharField(
        max_length=255,
        blank=True,
        help_text="Alternative description for accessibility and SEO."
    )
    upload_date = models.DateTimeField(
        auto_now_add=True,
        help_text="The date and time this asset was uploaded."
    )
    file_size = models.PositiveIntegerField(
        editable=False,
        help_text="File size in bytes."
    )
    width = models.PositiveIntegerField(
        null=True,
        blank=True,
        editable=False,
        help_text="Image width in pixels (raster images only)."
    )
    height = models.PositiveIntegerField(
        null=True,
        blank=True,
        editable=False,
        help_text="Image height in pixels (raster images only)."
    )

    class Meta:
        verbose_name = "Media Asset"
        verbose_name_plural = "Media Assets"
        ordering = ['-upload_date']

    def save(self, *args, **kwargs):
        # Auto-populate metadata on save
        if self.file:
            self.file_size = self.file.size
            if not self.original_filename:
                self.original_filename = os.path.basename(self.file.name)
            
            # Check file extension
            ext = os.path.splitext(self.file.name)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png', '.webp']:
                try:
                    # Open raster image to query dimensions
                    with Image.open(self.file) as img:
                        self.width, self.height = img.size
                except Exception:
                    # Fallback if image opening fails
                    self.width = None
                    self.height = None
            else:
                # SVGs do not have raster-based dimensions in Pillow
                self.width = None
                self.height = None
                
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Delete file from disk when model is deleted
        if self.file and os.path.exists(self.file.path):
            try:
                os.remove(self.file.path)
            except OSError:
                pass
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.original_filename
