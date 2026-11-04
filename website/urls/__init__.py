from django.urls import path, include
from django.views.defaults import page_not_found
from website import views

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("services/", views.services, name="services"),
    path("contact/", views.contact, name="contact"),
    path("thank-you/", views.thank_you, name="thank_you"),
    path("404/", page_not_found, {"exception": Exception("Page not Found")}, name="test_404"),
    path("category/<slug:category_slug>/", views.blog_list, name="blog_category"),
    path("blog/", include("website.urls.blog")),
    path("case-study/", include("website.urls.case_studies")),
    # Top-level SEO-friendly URLs for both Blog Posts and Service Pages
    # The blog_detail name has been moved to website.urls.blog. dynamic_page_detail now handles 301 redirects for legacy blog URLs.
    path("<slug:slug>/", views.dynamic_page_detail, name="dynamic_page_detail"),
    path("<slug:slug>/", views.dynamic_page_detail, name="service_detail"),
]


