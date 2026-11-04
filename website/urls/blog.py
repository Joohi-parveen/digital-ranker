from django.urls import path
from website import views

urlpatterns = [
    path("", views.blog_list, name="blog_list"),
    path("create/", views.blog_create, name="blog_create"),
    path("<slug:slug>/edit/", views.blog_update, name="blog_update"),
    path("<slug:slug>/delete/", views.blog_delete, name="blog_delete"),
    # Map the blog detail directly to /blog/<slug>/
    path("<slug:slug>/", views.blog_detail, name="blog_detail"),
]

