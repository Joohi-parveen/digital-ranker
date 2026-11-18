from django.core.cache import cache
from website.models.seo import PageSEOSetting
from website.models import Service

def seo_context(request):
    """
    Django context processor that determines the current page based on request.path,
    and returns its associated PageSEOSetting record to the template context.
    """
    path = request.path
    clean_path = path.strip('/')
    page_name = 'home'
    is_dynamic_service = False
    
    # Map the URL path prefix to page_name choices defined in PageSEOSetting
    if path == '/' or not clean_path:
        page_name = 'home'
    elif path.startswith('/about/'):
        page_name = 'about'
    elif path.startswith('/services/'):
        parts = clean_path.split('/')
        if len(parts) > 1:
            page_name = f"service_{parts[1]}"
        else:
            page_name = 'services'
    elif path.startswith('/blog/'):
        if clean_path == 'blog':
            page_name = 'blog'
        else:
            # For individual blog posts, we want to use the BlogPost's own SEO fields
            page_name = 'blog_post'
    elif path.startswith('/contact/'):
        page_name = 'contact'
    elif path.startswith('/team/'):
        page_name = 'team'
    elif path.startswith('/case-study/'):
        if clean_path == 'case-study':
            page_name = 'case_studies'
        else:
            page_name = 'case_study_detail'
    else:
        # Check if the clean_path corresponds to a Service (single-segment or multi-segment like india/delhi-ncr/...)
        if Service.objects.filter(slug=clean_path).exists():
            page_name = f"service_{clean_path}"
            is_dynamic_service = True
        else:
            # Check legacy PageSEOSetting for single-segment (e.g. service_ai-seo-agency-india)
            parts = clean_path.split('/')
            if len(parts) == 1 and parts[0]:
                page_name = f"service_{parts[0]}"
            else:
                page_name = 'other'

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
            # If the current page is not home, this is definitely a fallback
            seo_is_fallback = (page_name != 'home')
        
        # If it's a dynamic service that has its own model SEO fields, treat site settings as fallback
        if is_dynamic_service:
            seo_is_fallback = True

        # Cache for 24 hours (86400 seconds)
        cache.set(cache_key, (seo_settings, seo_is_fallback), 86400)
        
    return {
        'seo_settings': seo_settings,
        'seo_is_fallback': seo_is_fallback
    }

