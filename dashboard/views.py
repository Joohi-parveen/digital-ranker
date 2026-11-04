import os
from functools import wraps
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.core.paginator import Paginator
from django.urls import reverse
from urllib.parse import urlencode
from django.utils.http import url_has_allowed_host_and_scheme

from website.models import BlogPost, BlogCategory, ContactMessage, Service, CaseStudy, BlockedIP
from website.models.seo import PageSEOSetting
from website.forms import BlogPostForm, BlogCategoryForm, ServiceForm, CaseStudyForm, BlogFAQFormSet, CaseStudyFAQFormSet
from dashboard.forms import DashboardLoginForm, PageSEOSettingForm, BlockedIPForm


def staff_required(view_func):
    """
    Decorator that checks if the user is authenticated and is a staff member.
    Wraps the view function using functools.wraps to preserve docstrings/names.
    Redirects unauthenticated users to login with the '?next=' query parameter.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            login_url = reverse('dashboard_login')
            query_string = urlencode({'next': request.path})
            return redirect(f"{login_url}?{query_string}")
        if not request.user.is_staff:
            messages.error(request, "Permission denied. Staff access required.")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view



def dashboard_login(request):
    """
    Custom login view for the CMS dashboard.
    Demonstrates security handling of '?next=' query parameter redirects
    using standard scheme verification to prevent open redirect vulnerabilities.
    """
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('dashboard_index')

    if request.method == 'POST':
        form = DashboardLoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user and isinstance(user, User) and user.is_staff:
                auth_login(request, user)
                messages.success(request, f"Welcome back, {user.first_name or user.username}!")
                
                # Validate the redirect target to secure redirect path
                redirect_to = request.GET.get('next') or request.POST.get('next')
                if redirect_to and url_has_allowed_host_and_scheme(
                    url=redirect_to, 
                    allowed_hosts={request.get_host()}
                ):
                    return redirect(redirect_to)
                
                return redirect('dashboard_index')
            else:
                messages.error(request, "Access denied. Only staff members can access the dashboard.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = DashboardLoginForm()

    return render(request, 'dashboard/login.html', {'form': form})



def dashboard_logout(request):
    """
    Logs out the user and redirects to login page.
    """
    auth_logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('dashboard_login')


@staff_required
def dashboard_index(request):
    """
    Dashboard landing page displaying system statistics and recent entries.
    """
    blog_qs = BlogPost.objects.all()
    leads_qs = ContactMessage.objects.all()
    categories_qs = BlogCategory.objects.all()
    services_qs = Service.objects.all()

    # Aggregate stats
    total_posts = blog_qs.count()
    published_posts = blog_qs.filter(status='PUBLISHED').count()
    draft_posts = blog_qs.filter(status='DRAFT').count()
    total_categories = categories_qs.count()
    total_services = services_qs.count()
    
    total_views = blog_qs.aggregate(Sum('views_count'))['views_count__sum'] or 0
    total_leads = leads_qs.count()

    # Recent lists
    recent_posts = blog_qs.select_related('category', 'author').order_by('-created_at')[:5]
    recent_leads = leads_qs.order_by('-created_at')[:5]

    context = {
        'total_posts': total_posts,
        'published_posts': published_posts,
        'draft_posts': draft_posts,
        'total_categories': total_categories,
        'total_services': total_services,
        'total_views': total_views,
        'total_leads': total_leads,
        'recent_posts': recent_posts,
        'recent_leads': recent_leads,
        'active_tab': 'dashboard'
    }
    return render(request, 'dashboard/index.html', context)


@staff_required
def dashboard_blog_list(request):
    """
    Tabular list of blog posts in the CMS with search, status filter, and category filter.
    """
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    category_filter = request.GET.get('category', '').strip()
    
    posts = BlogPost.objects.select_related('category', 'author').all()
    
    if query:
        posts = posts.filter(
            Q(title__icontains=query) | 
            Q(content__icontains=query) | 
            Q(excerpt__icontains=query)
        )
    if status_filter in ['PUBLISHED', 'DRAFT']:
        posts = posts.filter(status=status_filter)
    if category_filter:
        posts = posts.filter(category__slug=category_filter)

    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    categories = BlogCategory.objects.all().order_by('name')

    context = {
        'page_obj': page_obj,
        'query': query,
        'status_filter': status_filter,
        'category_filter': category_filter,
        'categories': categories,
        'active_tab': 'blogs'
    }
    return render(request, 'dashboard/blog_list.html', context)


@staff_required
def dashboard_blog_create(request):
    """
    Dashboard view to create a new blog post.
    """
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES)
        formset = BlogFAQFormSet(request.POST, request.FILES)
        if form.is_valid() and formset.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            formset.instance = post
            formset.save()
            messages.success(request, f"Blog post '{post.title}' created successfully!")
            return redirect('dashboard_blog_list')
        else:
            messages.error(request, "Failed to create post. Please check the errors below.")
    else:
        form = BlogPostForm()
        formset = BlogFAQFormSet()

    context = {
        'form': form,
        'formset': formset,
        'action': 'Create',
        'active_tab': 'blogs'
    }
    return render(request, 'dashboard/blog_form.html', context)


@staff_required
def dashboard_blog_update(request, slug):
    """
    Dashboard view to edit an existing blog post.
    """
    post = get_object_or_404(BlogPost, slug=slug)
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES, instance=post)
        formset = BlogFAQFormSet(request.POST, request.FILES, instance=post)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, f"Blog post '{post.title}' updated successfully!")
            return redirect('dashboard_blog_list')
        else:
            messages.error(request, "Failed to update post. Please check the errors below.")
    else:
        form = BlogPostForm(instance=post)
        formset = BlogFAQFormSet(instance=post)

    context = {
        'form': form,
        'formset': formset,
        'post': post,
        'action': 'Update',
        'active_tab': 'blogs'
    }
    return render(request, 'dashboard/blog_form.html', context)


@staff_required
def dashboard_blog_delete(request, slug):
    """
    Delete a blog post.
    """
    post = get_object_or_404(BlogPost, slug=slug)
    post_title = post.title
    post.delete()
    messages.success(request, f"Blog post '{post_title}' has been deleted.")
    return redirect('dashboard_blog_list')


# ==========================================
# Blog Category Management Views
# ==========================================

@staff_required
def dashboard_category_list(request):
    """
    Tabular list of blog categories in the CMS with blog count and search.
    """
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()

    categories = BlogCategory.objects.annotate(blog_count=Count('blog_posts')).order_by('name')

    if query:
        categories = categories.filter(
            Q(name__icontains=query) |
            Q(slug__icontains=query) |
            Q(description__icontains=query)
        )
    if status_filter in ['ACTIVE', 'INACTIVE']:
        categories = categories.filter(status=status_filter)

    paginator = Paginator(categories, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'status_filter': status_filter,
        'active_tab': 'categories'
    }
    return render(request, 'dashboard/category_list.html', context)


@staff_required
def dashboard_category_create(request):
    """
    Dashboard view to create a new blog category.
    """
    if request.method == 'POST':
        form = BlogCategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f"Category '{category.name}' created successfully!")
            return redirect('dashboard_category_list')
        else:
            messages.error(request, "Failed to create category. Please check the errors below.")
    else:
        form = BlogCategoryForm()

    context = {
        'form': form,
        'action': 'Create',
        'active_tab': 'categories'
    }
    return render(request, 'dashboard/category_form.html', context)


@staff_required
def dashboard_category_update(request, slug):
    """
    Dashboard view to edit an existing blog category.
    """
    category = get_object_or_404(BlogCategory, slug=slug)
    if request.method == 'POST':
        form = BlogCategoryForm(request.POST, instance=category)
        if form.is_valid():
            category = form.save()
            messages.success(request, f"Category '{category.name}' updated successfully!")
            return redirect('dashboard_category_list')
        else:
            messages.error(request, "Failed to update category. Please check the errors below.")
    else:
        form = BlogCategoryForm(instance=category)

    context = {
        'form': form,
        'category': category,
        'action': 'Update',
        'active_tab': 'categories'
    }
    return render(request, 'dashboard/category_form.html', context)


@staff_required
def dashboard_category_delete(request, slug):
    """
    Delete a blog category. Associated blog posts will have their category set to null.
    """
    category = get_object_or_404(BlogCategory, slug=slug)
    cat_name = category.name
    category.delete()
    messages.success(request, f"Category '{cat_name}' has been deleted.")
    return redirect('dashboard_category_list')


@staff_required
def dashboard_lead_list(request):
    """
    Tabular list of contact inquiries in the CMS.
    """
    query = request.GET.get('q', '').strip()
    leads = ContactMessage.objects.all()

    if query:
        leads = leads.filter(
            Q(name__icontains=query) |
            Q(subject__icontains=query) |
            Q(email__icontains=query) |
            Q(ip_address__icontains=query)
        )

    paginator = Paginator(leads, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'active_tab': 'leads'
    }
    return render(request, 'dashboard/lead_list.html', context)


@staff_required
def dashboard_lead_detail(request, pk):
    """
    Detail page for a single contact inquiry.
    """
    lead = get_object_or_404(ContactMessage, pk=pk)
    is_blocked = False
    if lead.ip_address:
        is_blocked = BlockedIP.objects.filter(ip_address=lead.ip_address, is_active=True).exists()
    context = {
        'lead': lead,
        'is_blocked': is_blocked,
        'active_tab': 'leads'
    }
    return render(request, 'dashboard/lead_detail.html', context)


@staff_required
def dashboard_lead_block_ip(request, pk):
    """
    Direct 1-click action to block the IP address of a spam/malicious lead.
    """
    lead = get_object_or_404(ContactMessage, pk=pk)
    if not lead.ip_address:
        messages.error(request, "This lead does not have a recorded IP address.")
        return redirect('dashboard_lead_detail', pk=pk)

    blocked_ip, created = BlockedIP.objects.get_or_create(
        ip_address=lead.ip_address,
        defaults={
            'reason': f"Blocked from Lead #{lead.pk} ({lead.name})",
            'is_active': True,
            'created_by': request.user if request.user.is_authenticated else None,
        }
    )
    if not created and not blocked_ip.is_active:
        blocked_ip.is_active = True
        blocked_ip.reason = f"Re-blocked from Lead #{lead.pk} ({lead.name})"
        blocked_ip.save()
        messages.success(request, f"IP {lead.ip_address} has been re-activated in the blocklist.")
    elif created:
        messages.success(request, f"IP {lead.ip_address} has been successfully added to the blocklist.")
    else:
        messages.info(request, f"IP {lead.ip_address} is already active in the blocklist.")

    return redirect('dashboard_lead_detail', pk=pk)


@staff_required
def dashboard_lead_delete(request, pk):
    """
    Delete a contact inquiry/lead.
    """
    lead = get_object_or_404(ContactMessage, pk=pk)
    lead.delete()
    messages.success(request, "Lead deleted successfully.")
    return redirect('dashboard_lead_list')



# -------------------------------------------------------------
# Service Management Views
# -------------------------------------------------------------

@staff_required
def dashboard_service_list(request):
    """
    Tabular list of Services in the CMS with search and status filtering.
    """
    services = Service.objects.all().order_by('-created_at')

    # 1. Search Query
    query = request.GET.get('q', '').strip()
    if query:
        services = services.filter(
            Q(title__icontains=query) |
            Q(slug__icontains=query) |
            Q(content__icontains=query) |
            Q(meta_title__icontains=query)
        )

    # 2. Status Filter
    status_filter = request.GET.get('status', '').strip().upper()
    if status_filter in ['PUBLISHED', 'DRAFT']:
        services = services.filter(status=status_filter)

    # 3. Pagination
    paginator = Paginator(services, 15)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    total_services = Service.objects.count()
    published_services = Service.objects.filter(status='PUBLISHED').count()
    draft_services = Service.objects.filter(status='DRAFT').count()

    context = {
        'page_obj': page_obj,
        'query': query,
        'status_filter': status_filter,
        'total_services': total_services,
        'published_services': published_services,
        'draft_services': draft_services,
        'active_tab': 'services',
    }
    return render(request, 'dashboard/service_list.html', context)


@staff_required
def dashboard_service_create(request):
    """
    Dashboard view to create a new Service page.
    """
    if request.method == 'POST':
        form = ServiceForm(request.POST, request.FILES)
        if form.is_valid():
            service = form.save()
            messages.success(request, f"Service '{service.title}' created successfully!")
            return redirect('dashboard_service_list')
        else:
            messages.error(request, "Please correct the errors in the form below.")
    else:
        form = ServiceForm()

    context = {
        'form': form,
        'action': 'Add',
        'active_tab': 'services_add',
    }
    return render(request, 'dashboard/service_form.html', context)


@staff_required
def dashboard_service_update(request, slug):
    """
    Dashboard view to edit an existing Service page.
    """
    service = get_object_or_404(Service, slug=slug)
    if request.method == 'POST':
        form = ServiceForm(request.POST, request.FILES, instance=service)
        if form.is_valid():
            service = form.save()
            messages.success(request, f"Service '{service.title}' updated successfully!")
            return redirect('dashboard_service_list')
        else:
            messages.error(request, "Please correct the errors in the form below.")
    else:
        form = ServiceForm(instance=service)

    context = {
        'form': form,
        'service': service,
        'action': 'Edit',
        'active_tab': 'services',
    }
    return render(request, 'dashboard/service_form.html', context)


@staff_required
def dashboard_service_delete(request, slug):
    """
    Delete a Service page.
    """
    service = get_object_or_404(Service, slug=slug)
    service_title = service.title
    service.delete()
    messages.success(request, f"Service '{service_title}' has been deleted.")
    return redirect('dashboard_service_list')


# -------------------------------------------------------------
# SEO Management Views (Static / Custom Pages)
# -------------------------------------------------------------

def get_all_configurable_pages():
    """
    Returns the list of static / custom core pages configurable in SEO Management.
    Dynamic Services and Blog Posts manage their own SEO metadata within their respective CMS modules.
    """
    return [
        ('home', 'Home Page'),
        ('about', 'About Page'),
        ('services', 'Services Hub Page'),
        ('blog', 'Blog List Page'),
        ('contact', 'Contact Page'),
        ('team', 'Team Page'),
    ]


@staff_required
def dashboard_seo_list(request):
    """
    Renders the SEO settings management dashboard homepage.
    """
    valid_pages = get_all_configurable_pages()
    settings_dict = {s.page_name: s for s in PageSEOSetting.objects.all()}
    
    pages_data = []
    for page_code, page_label in valid_pages:
        setting = settings_dict.get(page_code)
        pages_data.append({
            'code': page_code,
            'label': page_label,
            'is_configured': setting is not None,
            'setting': setting
        })
        
    context = {
        'pages_data': pages_data,
        'active_tab': 'seo',
    }
    return render(request, 'dashboard/seo_list.html', context)


@staff_required
def dashboard_seo_edit(request, page_name):
    """
    Renders and processes the form to update SEO Settings for a single page.
    Uses get_or_create to automatically initialize the page's record if it doesn't exist yet.
    """
    valid_pages = dict(get_all_configurable_pages())
    if page_name not in valid_pages:
        messages.error(request, "Invalid page selected.")
        return redirect('dashboard_seo_list')
        
    # Automatically get or initialize the SEO record for the page
    seo_setting, created = PageSEOSetting.objects.get_or_create(page_name=page_name)
    
    if request.method == 'POST':
        form = PageSEOSettingForm(request.POST, request.FILES, instance=seo_setting)
        if form.is_valid():
            form.save()
            messages.success(request, f"SEO Settings for '{valid_pages[page_name]}' updated successfully!")
            return redirect('dashboard_seo_list')
    else:
        form = PageSEOSettingForm(instance=seo_setting)
        
    context = {
        'form': form,
        'page_name': page_name,
        'page_title': valid_pages[page_name],
        'seo_setting': seo_setting,
        'active_tab': 'seo',
    }
    return render(request, 'dashboard/seo_form.html', context)


# -------------------------------------------------------------
# Case Study Management Views
# -------------------------------------------------------------

@staff_required
def dashboard_case_study_list(request):
    """
    Tabular list of Case Studies in the CMS.
    """
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip().upper()
    
    case_studies = CaseStudy.objects.all().order_by('-created_at')
    
    if query:
        case_studies = case_studies.filter(
            Q(title__icontains=query) | 
            Q(client__icontains=query) | 
            Q(challenge__icontains=query)
        )
    if status_filter in ['PUBLISHED', 'DRAFT']:
        case_studies = case_studies.filter(status=status_filter)

    paginator = Paginator(case_studies, 15)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    total_case_studies = CaseStudy.objects.count()
    published_case_studies = CaseStudy.objects.filter(status='PUBLISHED').count()
    draft_case_studies = CaseStudy.objects.filter(status='DRAFT').count()

    context = {
        'page_obj': page_obj,
        'query': query,
        'status_filter': status_filter,
        'total_case_studies': total_case_studies,
        'published_case_studies': published_case_studies,
        'draft_case_studies': draft_case_studies,
        'active_tab': 'case_studies'
    }
    return render(request, 'dashboard/case_study_list.html', context)


@staff_required
def dashboard_case_study_create(request):
    """
    Dashboard view to create a new case study.
    """
    if request.method == 'POST':
        form = CaseStudyForm(request.POST, request.FILES)
        formset = CaseStudyFAQFormSet(request.POST, request.FILES)
        if form.is_valid() and formset.is_valid():
            case_study = form.save(commit=False)
            case_study.author = request.user
            case_study.save()
            formset.instance = case_study
            formset.save()
            messages.success(request, f"Case study '{case_study.title}' created successfully!")
            return redirect('dashboard_case_study_list')
        else:
            messages.error(request, "Failed to create case study. Please check the errors below.")
    else:
        form = CaseStudyForm()
        formset = CaseStudyFAQFormSet()

    context = {
        'form': form,
        'formset': formset,
        'action': 'Create',
        'active_tab': 'case_studies_add'
    }
    return render(request, 'dashboard/case_study_form.html', context)


@staff_required
def dashboard_case_study_update(request, slug):
    """
    Dashboard view to edit an existing case study.
    """
    case_study = get_object_or_404(CaseStudy, slug=slug)
    if request.method == 'POST':
        form = CaseStudyForm(request.POST, request.FILES, instance=case_study)
        formset = CaseStudyFAQFormSet(request.POST, request.FILES, instance=case_study)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, f"Case study '{case_study.title}' updated successfully!")
            return redirect('dashboard_case_study_list')
        else:
            messages.error(request, "Failed to update case study. Please check the errors below.")
    else:
        form = CaseStudyForm(instance=case_study)
        formset = CaseStudyFAQFormSet(instance=case_study)

    context = {
        'form': form,
        'formset': formset,
        'case_study': case_study,
        'action': 'Update',
        'active_tab': 'case_studies'
    }
    return render(request, 'dashboard/case_study_form.html', context)


@staff_required
def dashboard_case_study_delete(request, slug):
    """
    Delete a case study.
    """
    case_study = get_object_or_404(CaseStudy, slug=slug)
    case_study_title = case_study.title
    case_study.delete()
    messages.success(request, f"Case study '{case_study_title}' has been deleted.")
    return redirect('dashboard_case_study_list')


# -------------------------------------------------------------
# Blocked IP Management Views
# -------------------------------------------------------------

@staff_required
def dashboard_blocked_ip_list(request):
    """
    Dashboard view to list, search, and manage blocked IP addresses.
    """
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip().lower()

    blocked_ips = BlockedIP.objects.select_related('created_by').all().order_by('-created_at')

    if query:
        blocked_ips = blocked_ips.filter(
            Q(ip_address__icontains=query) |
            Q(reason__icontains=query)
        )

    if status_filter == 'active':
        blocked_ips = blocked_ips.filter(is_active=True)
    elif status_filter == 'inactive':
        blocked_ips = blocked_ips.filter(is_active=False)

    paginator = Paginator(blocked_ips, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    total_count = BlockedIP.objects.count()
    active_count = BlockedIP.objects.filter(is_active=True).count()
    inactive_count = total_count - active_count
    total_blocked_attempts = BlockedIP.objects.aggregate(total=Sum('blocked_attempts_count'))['total'] or 0

    add_form = BlockedIPForm()

    context = {
        'page_obj': page_obj,
        'query': query,
        'status_filter': status_filter,
        'total_count': total_count,
        'active_count': active_count,
        'inactive_count': inactive_count,
        'total_blocked_attempts': total_blocked_attempts,
        'add_form': add_form,
        'active_tab': 'blocked_ips'
    }
    return render(request, 'dashboard/blocked_ip_list.html', context)


@staff_required
def dashboard_blocked_ip_create(request):
    """
    Create a new blocked IP from the dashboard modal or page.
    """
    if request.method == 'POST':
        form = BlockedIPForm(request.POST)
        if form.is_valid():
            blocked_ip = form.save(commit=False)
            blocked_ip.created_by = request.user
            blocked_ip.save()
            messages.success(request, f"IP address '{blocked_ip.ip_address}' successfully added to blocklist.")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{error}")
    return redirect('dashboard_blocked_ip_list')


@staff_required
def dashboard_blocked_ip_toggle(request, pk):
    """
    Toggle an IP address active / inactive status.
    """
    blocked_ip = get_object_or_404(BlockedIP, pk=pk)
    blocked_ip.is_active = not blocked_ip.is_active
    blocked_ip.save()
    status_str = "activated" if blocked_ip.is_active else "deactivated"
    messages.success(request, f"Block on IP '{blocked_ip.ip_address}' has been {status_str}.")
    return redirect('dashboard_blocked_ip_list')


@staff_required
def dashboard_blocked_ip_delete(request, pk):
    """
    Permanently remove an IP address from the blocklist.
    """
    blocked_ip = get_object_or_404(BlockedIP, pk=pk)
    ip_addr = blocked_ip.ip_address
    blocked_ip.delete()
    messages.success(request, f"IP address '{ip_addr}' has been removed from the blocklist.")
    return redirect('dashboard_blocked_ip_list')

