from django.urls import path
from media_library import views

urlpatterns = [
    path('', views.media_list, name='media_list'),
    path('<int:pk>/delete/', views.media_delete, name='media_delete'),
]
