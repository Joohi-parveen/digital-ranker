from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify

class CaseStudy(models.Model):
    """
    Represents a case study project in the CMS.
    """
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('PUBLISHED', 'Published'),
    )

    title = models.CharField(max_length=200, help_text="Project title")
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    author = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='case_studies',
        help_text="The author of the case study",
        null=True,
        blank=True
    )
    
    # Custom fields for Case Study
    client = models.CharField(max_length=200, blank=True, help_text="Client or Industry name")
    featured_image = models.ImageField(
        upload_to='case_studies/images/', 
        blank=True, 
        null=True,
        help_text="Featured image for the case study"
    )
    

    
    content = models.TextField(blank=True, help_text="Full detailed overview (optional if using Challenge/Solution/Results)")
    
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='DRAFT'
    )
    is_featured = models.BooleanField(
        default=False,
        help_text="Show this case study in featured sections"
    )
    views_count = models.PositiveIntegerField(default=0, editable=False)
    
    # SEO Fields
    meta_title = models.CharField(
        max_length=100, 
        blank=True, 
        help_text="SEO Meta Title (falls back to title if blank)"
    )
    meta_description = models.TextField(
        max_length=160, 
        blank=True, 
        help_text="SEO Meta Description (150-160 characters)"
    )
    meta_keywords = models.CharField(
        max_length=255, 
        blank=True, 
        help_text="SEO Meta Keywords (comma separated)"
    )
    schema_markup = models.TextField(
        blank=True,
        help_text="JSON-LD Schema markup for the case study"
    )
    
    # FAQ Fields
    faq_heading = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        help_text="Optional custom heading for the FAQ section (e.g., 'Frequently Asked Questions')"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Case Study"
        verbose_name_plural = "Case Studies"

    def __str__(self):
        return self.title

    @property
    def get_schema_markup_list(self):
        import json
        if not self.schema_markup:
            return []
        
        schema = self.schema_markup.strip()
        
        # Strip script tags for legacy data if present
        if schema.lower().startswith('<script') and schema.lower().endswith('</script>'):
            import re
            match = re.search(r'<script[^>]*>(.*?)</script>', schema, re.DOTALL | re.IGNORECASE)
            if match:
                schema = match.group(1).strip()
                
        if not schema:
            return []
            
        try:
            data = json.loads(schema)
            if isinstance(data, list):
                return [json.dumps(item, indent=2) for item in data]
            else:
                return [json.dumps(data, indent=2)]
        except json.JSONDecodeError:
            # Fallback to returning the raw string if parsing fails
            return [schema]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title, allow_unicode=True)
            slug = base_slug
            counter = 1
            while CaseStudy.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        
        super().save(*args, **kwargs)

class CaseStudyFAQ(models.Model):
    """
    Represents a Frequently Asked Question associated with a specific case study.
    """
    case_study = models.ForeignKey(
        CaseStudy, 
        on_delete=models.CASCADE, 
        related_name='faqs'
    )
    question = models.CharField(max_length=255)
    answer = models.TextField()
    order = models.PositiveIntegerField(
        default=0,
        help_text="Controls the display order of the FAQs"
    )

    class Meta:
        ordering = ['order', 'id']
        verbose_name = "Case Study FAQ"
        verbose_name_plural = "Case Study FAQs"

    def __str__(self):
        return f"{self.case_study.title} - {self.question}"
