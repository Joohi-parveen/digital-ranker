"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# pyrefly: ignore [missing-import]
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve

from django.contrib.sitemaps.views import sitemap
from website.sitemaps import StaticViewSitemap, BlogPostSitemap, ServiceSitemap, CaseStudySitemap
from django.http import HttpResponse
from django.views.decorators.http import require_GET

sitemaps = {
    'static': StaticViewSitemap,
    'blog': BlogPostSitemap,
    'service': ServiceSitemap,
    'case_study': CaseStudySitemap,
}

@require_GET
def robots_txt(request):
    lines = """# robots.txt file (AI Digital Ranker)

User-agent: *
Allow: /
Disallow: /admin/
Disallow: /dashboard/
Disallow: /search/
Disallow: /?s=
Disallow: /tag/
Disallow: /author/
Disallow: /cgi-bin/


# ------------------------------------------------------------------------------
# OpenAI Crawlers
# ------------------------------------------------------------------------------

# Training crawler — builds datasets for GPT model development
User-agent: GPTBot
Allow: /

# Search indexing crawler — powers ChatGPT Search citations
User-agent: OAI-SearchBot
Allow: /

# User-triggered fetcher — activated when a human pastes a URL into ChatGPT
User-agent: ChatGPT-User
Allow: /


# ------------------------------------------------------------------------------
# Anthropic Crawlers
# ------------------------------------------------------------------------------

# Training crawler — used for Claude model training data collection
User-agent: ClaudeBot
Allow: /

# Search indexing crawler — supports Claude web search
User-agent: Claude-SearchBot
Allow: /

# User-triggered fetcher — activated when a Claude user requests a specific page
User-agent: Claude-User
Allow: /


# ------------------------------------------------------------------------------
# Perplexity Crawlers
# ------------------------------------------------------------------------------

# Primary indexing crawler — used for Perplexity AI search
User-agent: PerplexityBot
Allow: /

# User-triggered retrieval — fetches pages when a Perplexity user clicks a citation
User-agent: Perplexity-User
Allow: /


# ------------------------------------------------------------------------------
# Google AI Systems
# ------------------------------------------------------------------------------

# Controls Gemini model training and Google AI data collection
User-agent: Google-Extended
Allow: /

# Google AI crawler for AI-related content retrieval
User-agent: Googlebot-Extended
Allow: /


# ------------------------------------------------------------------------------
# Meta AI
# ------------------------------------------------------------------------------

User-agent: Meta-ExternalAgent
Allow: /

User-agent: FacebookBot
Allow: /


# ------------------------------------------------------------------------------
# Common Crawl
# ------------------------------------------------------------------------------

# Common Crawl crawler used for web datasets and research
User-agent: CCBot
Allow: /


# ------------------------------------------------------------------------------
# Other AI & Search Crawlers
# ------------------------------------------------------------------------------

# Amazon
User-agent: Amazonbot
Allow: /

# Apple
User-agent: Applebot
Allow: /

User-agent: Applebot-Extended
Allow: /

# ByteDance
User-agent: Bytespider
Allow: /

# Cohere
User-agent: cohere-ai
Allow: /


# ------------------------------------------------------------------------------
# Sitemap
# ------------------------------------------------------------------------------

Sitemap: """ + request.build_absolute_uri('/sitemap.xml')
    
    return HttpResponse(lines, content_type="text/plain")

urlpatterns = [
    # path("admin/", admin.site.urls),
    path("dashboard/", include("dashboard.urls")),
    path("", include("website.urls")),
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django.contrib.sitemaps.views.sitemap"),
    path("robots.txt", robots_txt),
]



