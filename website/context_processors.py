from django.core.cache import cache
from website.models.seo import PageSEOSetting

def seo_context(request):
    """
    Django context processor that determines the current page based on request.path,
    and returns its associated PageSEOSetting record to the template context.
    """
    path = request.path
    page_name = 'home'
    
    # Map the URL path prefix to page_name choices defined in PageSEOSetting
    if path == '/':
        page_name = 'home'
    elif path.startswith('/about/'):
        page_name = 'about'
    elif path.startswith('/services/'):
        parts = path.strip('/').split('/')
        if len(parts) > 1:
            page_name = f"service_{parts[1]}"
        else:
            page_name = 'services'
    elif path.startswith('/blog/'):
        if path == '/blog/' or path == '/blog':
            page_name = 'blog'
        else:
            # For individual blog posts, we want to use the BlogPost's own SEO fields
            page_name = 'blog_post'
    elif path.startswith('/contact/'):
        page_name = 'contact'
    elif path.startswith('/team/'):
        page_name = 'team'
    else:
        # Check single-segment slug (e.g. /ai-seo-agency-india/)
        parts = path.strip('/').split('/')
        if len(parts) == 1 and parts[0]:
            page_name = f"service_{parts[0]}"
        else:
            page_name = 'home'
        
    cache_key = f"seo_settings_{page_name}"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        seo_settings, seo_is_fallback = cached_data
    else:
        try:
            seo_settings = PageSEOSetting.objects.get(page_name=page_name)
            seo_is_fallback = False
        except PageSEOSetting.DoesNotExist:
            # Fallback to home page SEO setting for global site_title/favicon
            seo_settings = PageSEOSetting.objects.filter(page_name='home').first()
            seo_is_fallback = True
        
        # Cache for 24 hours (86400 seconds)
        cache.set(cache_key, (seo_settings, seo_is_fallback), 86400)
        
    return {
        'seo_settings': seo_settings,
        'seo_is_fallback': seo_is_fallback
    }

