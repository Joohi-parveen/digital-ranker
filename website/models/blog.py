# pyrefly: ignore [missing-import]
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify

class BlogCategory(models.Model):
    """
    Represents a category for organizing blog posts in the CMS.
    """
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
    )

    name = models.CharField(max_length=100, unique=True, help_text="Unique category name")
    slug = models.SlugField(max_length=120, unique=True, blank=True, help_text="URL fragment for category")
    description = models.TextField(blank=True, help_text="Optional category description")
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='ACTIVE',
        help_text="Active categories are visible to public and selectable in blog editor"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = "Blog Category"
        verbose_name_plural = "Blog Categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while BlogCategory.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


class BlogPost(models.Model):
    """
    Represents a blog post in the CMS.
    """
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('PUBLISHED', 'Published'),
    )

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    category = models.ForeignKey(
        BlogCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='blog_posts',
        help_text="Category of the blog post"
    )
    author = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='blog_posts',
        help_text="The author of the blog post"
    )
    content = models.TextField()
    excerpt = models.TextField(
        max_length=500, 
        blank=True, 
        help_text="A short summary of the post for listing views."
    )
    featured_image = models.ImageField(
        upload_to='blog/images/', 
        blank=True, 
        null=True,
        help_text="Featured image for the blog post"
    )
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='DRAFT'
    )
    is_featured = models.BooleanField(
        default=False,
        help_text="Show this post in featured sections"
    )
    views_count = models.PositiveIntegerField(default=0, editable=False)
    
    # SEO Fields
    meta_title = models.CharField(
        max_length=100, 
        blank=True, 
        help_text="SEO Meta Title (falls back to post title if blank)"
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
        help_text="JSON-LD Schema markup for the blog post"
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
        verbose_name = "Blog Post"
        verbose_name_plural = "Blog Posts"

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
        # WHY this exists: This custom save hook automatically handles URL slug generation
        # so the content author doesn't have to write one manually.
        # WHEN it runs: Executes every time a BlogPost instance is saved (created or updated).
        # WHICH files interact: Triggered by forms.py and views (dashboard/views.py, website/views/blog.py).
        if not self.slug:
            # Step 1: Normalize the title to a URL-friendly slug (e.g. "My First Post!" -> "my-first-post")
            # We use allow_unicode=True to preserve characters like smart quotes instead of dropping them.
            base_slug = slugify(self.title, allow_unicode=True)
            slug = base_slug
            counter = 1
            # Step 2: Ensure unique slug by checking if it already exists in the database.
            # Industry note: In massive high-traffic systems, querying inside a loop can cause performance overhead.
            # However, for a standard CMS, this is a clean and reliable way to prevent slug collision errors.
            while BlogPost.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        
        # Call the parent class's save() method to write the data to the database.
        super().save(*args, **kwargs)


# Cache invalidation signals
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache

@receiver([post_save, post_delete], sender=BlogPost)
def clear_homepage_blog_cache(sender, instance, **kwargs):
    """
    Clears the homepage latest posts cache whenever a BlogPost is created, updated, or deleted.
    """
    cache.delete('homepage_latest_posts')


class BlogFAQ(models.Model):
    """
    Represents a Frequently Asked Question associated with a specific blog post.
    """
    blog_post = models.ForeignKey(
        BlogPost, 
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
        verbose_name = "Blog FAQ"
        verbose_name_plural = "Blog FAQs"

    def __str__(self):
        return f"{self.blog_post.title} - {self.question}"
