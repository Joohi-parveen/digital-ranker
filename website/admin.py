from django.contrib import admin
from .models import BlogPost, BlogCategory, Service
from .models.seo import PageSEOSetting

@admin.register(PageSEOSetting)
class PageSEOSettingAdmin(admin.ModelAdmin):
    list_display = ('page_name', 'site_title', 'meta_title', 'robots_meta')
    search_fields = ('page_name', 'meta_title', 'meta_description')


@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    """
    Django Admin customization for Blog Categories.
    """
    list_display = ('name', 'slug', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    """
    Django Admin customization for dynamic Service pages.
    """
    list_display = ('title', 'slug', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at', 'updated_at')
    search_fields = ('title', 'slug', 'content', 'meta_title', 'meta_description')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ("Service Details", {
            "fields": ("title", "slug", "status", "content")
        }),
        ("Hero / Banner Content", {
            "fields": ("hero_heading", "hero_description", "hero_cta_text", "hero_cta_url", "hero_banner_image"),
            "description": "Configure the top banner headline, description, CTA, and background banner image."
        }),
        ("SEO Meta Tags", {
            "fields": ("meta_title", "meta_description", "meta_keywords", "robots_meta", "canonical_url"),
            "classes": ("collapse",),
            "description": "Configure search engine optimization tags for this service."
        }),
        ("Open Graph / Social Sharing", {
            "fields": ("og_title", "og_description", "og_image"),
            "classes": ("collapse",),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    actions = ['make_published', 'make_draft']

    class Media:
        js = (
            'https://cdnjs.cloudflare.com/ajax/libs/tinymce/6.8.3/tinymce.min.js',
            'assets/js/tinymce-admin-init.js',
        )

    @admin.action(description="Mark selected services as Published")
    def make_published(self, request, queryset):
        updated = queryset.update(status='PUBLISHED')
        self.message_user(request, f"{updated} services successfully marked as Published.")

    @admin.action(description="Mark selected services as Draft")
    def make_draft(self, request, queryset):
        updated = queryset.update(status='DRAFT')
        self.message_user(request, f"{updated} services successfully marked as Draft.")


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    """
    Advanced Django Admin customization for BlogPost CMS.
    """
    # 1. Columns shown in the blog list view
    list_display = ('title', 'category', 'author', 'status', 'is_featured', 'views_count', 'created_at')
    
    # 2. Filters on the right sidebar
    list_filter = ('status', 'category', 'is_featured', 'created_at', 'author')
    # 3. Search bar fields
    search_fields = ('title', 'content', 'excerpt', 'author__username', 'author__first_name', 'author__last_name')
    
    # 4. Auto-populate slug from title
    prepopulated_fields = {'slug': ('title',)}
    
    # 5. Breadcrumb date navigation at the top
    date_hierarchy = 'created_at'
    
    # 6. Read-only metadata fields
    readonly_fields = ('views_count', 'created_at', 'updated_at')
    
    # 7. Form layout grouping
    fieldsets = (
        ("Post Details", {
            "fields": ("title", "slug", "category", "author", "content", "excerpt", "featured_image")
        }),
        ("Status & Feature Settings", {
            "fields": ("status", "is_featured")
        }),
        ("SEO Meta Tags", {
            "fields": ("meta_title", "meta_description", "meta_keywords"),
            "classes": ("collapse",), # Collapsible fieldset
            "description": "Customize meta information for search engine optimization."
        }),
        ("System Timestamps", {
            "fields": ("views_count", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    # 8. Custom Bulk Actions
    actions = ['make_published', 'make_draft']

    class Media:
        js = (
            'https://cdnjs.cloudflare.com/ajax/libs/tinymce/6.8.3/tinymce.min.js',
            'assets/js/tinymce-admin-init.js',
        )

    @admin.action(description="Mark selected posts as Published")
    def make_published(self, request, queryset):
        updated = queryset.update(status='PUBLISHED')
        self.message_user(request, f"{updated} blog posts successfully marked as Published.")

    @admin.action(description="Mark selected posts as Draft")
    def make_draft(self, request, queryset):
        updated = queryset.update(status='DRAFT')
        self.message_user(request, f"{updated} blog posts successfully marked as Draft.")

