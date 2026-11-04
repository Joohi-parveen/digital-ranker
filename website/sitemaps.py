from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from website.models.blog import BlogPost
from website.models.service import Service
from website.models.case_study import CaseStudy

class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = 'monthly'

    def items(self):
        return ['home', 'about', 'services', 'contact']

    def location(self, item):
        return reverse(item)

class BlogPostSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        # Only published posts
        return BlogPost.objects.filter(status='PUBLISHED')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse('blog_detail', kwargs={'slug': obj.slug})

class ServiceSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        # Only published services, excluding those marked as noindex
        return Service.objects.filter(
            status='PUBLISHED',
            robots_meta__icontains='index'
        ).exclude(robots_meta__icontains='noindex')

    def lastmod(self, obj):
        return obj.updated_at

class CaseStudySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return CaseStudy.objects.filter(status='PUBLISHED')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse('case_study_detail', kwargs={'slug': obj.slug})
