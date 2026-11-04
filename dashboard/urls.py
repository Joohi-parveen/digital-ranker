from django.urls import path, include
from dashboard import views

urlpatterns = [
    # Dashboard index
    path('', views.dashboard_index, name='dashboard_index'),
    
    # Auth urls
    path('login/', views.dashboard_login, name='dashboard_login'),
    path('logout/', views.dashboard_logout, name='dashboard_logout'),
    
    # Blogs CRUD
    path('blogs/', views.dashboard_blog_list, name='dashboard_blog_list'),
    path('blogs/add/', views.dashboard_blog_create, name='dashboard_blog_create'),
    path('blogs/<slug:slug>/edit/', views.dashboard_blog_update, name='dashboard_blog_update'),
    path('blogs/<slug:slug>/delete/', views.dashboard_blog_delete, name='dashboard_blog_delete'),
    
    # Categories CRUD
    path('categories/', views.dashboard_category_list, name='dashboard_category_list'),
    path('categories/add/', views.dashboard_category_create, name='dashboard_category_create'),
    path('categories/<slug:slug>/edit/', views.dashboard_category_update, name='dashboard_category_update'),
    path('categories/<slug:slug>/delete/', views.dashboard_category_delete, name='dashboard_category_delete'),
    
    # Services CRUD
    path('services/', views.dashboard_service_list, name='dashboard_service_list'),
    path('services/add/', views.dashboard_service_create, name='dashboard_service_create'),
    path('services/<slug:slug>/edit/', views.dashboard_service_update, name='dashboard_service_update'),
    path('services/<slug:slug>/delete/', views.dashboard_service_delete, name='dashboard_service_delete'),
    
    # Case Studies CRUD
    path('case-studies/', views.dashboard_case_study_list, name='dashboard_case_study_list'),
    path('case-studies/add/', views.dashboard_case_study_create, name='dashboard_case_study_create'),
    path('case-studies/<slug:slug>/edit/', views.dashboard_case_study_update, name='dashboard_case_study_update'),
    path('case-studies/<slug:slug>/delete/', views.dashboard_case_study_delete, name='dashboard_case_study_delete'),
    
    # Leads / Contact Inquiries
    path('leads/', views.dashboard_lead_list, name='dashboard_lead_list'),
    path('leads/<int:pk>/', views.dashboard_lead_detail, name='dashboard_lead_detail'),
    path('leads/<int:pk>/block-ip/', views.dashboard_lead_block_ip, name='dashboard_lead_block_ip'),
    path('leads/<int:pk>/delete/', views.dashboard_lead_delete, name='dashboard_lead_delete'),

    # Blocked IPs Management
    path('blocked-ips/', views.dashboard_blocked_ip_list, name='dashboard_blocked_ip_list'),
    path('blocked-ips/add/', views.dashboard_blocked_ip_create, name='dashboard_blocked_ip_create'),
    path('blocked-ips/<int:pk>/toggle/', views.dashboard_blocked_ip_toggle, name='dashboard_blocked_ip_toggle'),
    path('blocked-ips/<int:pk>/delete/', views.dashboard_blocked_ip_delete, name='dashboard_blocked_ip_delete'),
    
    # SEO Management
    path('seo/', views.dashboard_seo_list, name='dashboard_seo_list'),
    path('seo/<str:page_name>/edit/', views.dashboard_seo_edit, name='dashboard_seo_edit'),
    
    # Media Library
    path('media/', include('media_library.urls')),

]
