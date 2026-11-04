# pyrefly: ignore [missing-import]
from django.shortcuts import render, get_object_or_404, redirect
# pyrefly: ignore [missing-import]
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
# pyrefly: ignore [missing-import]
from django.contrib.auth.decorators import login_required
# pyrefly: ignore [missing-import]
from django.db import models
# pyrefly: ignore [missing-import]
from django.db.models import Q, Count
from website.models import BlogPost, BlogCategory
from website.forms import BlogPostForm


def blog_list(request, category_slug=None):
    """
    Renders a paginated list of published blog posts.
    Supports searching by title and content, as well as filtering by category.
    """
    query = request.GET.get('q', '').strip()
    category_slug = category_slug or request.GET.get('category', '').strip()
    selected_category = None
    
    # 1. Base query: standard users see only PUBLISHED, staff users can see DRAFTs too
    if request.user.is_staff:
        posts_queryset = BlogPost.objects.select_related('category', 'author').all()
    else:
        posts_queryset = BlogPost.objects.select_related('category', 'author').filter(status='PUBLISHED')

    # 2. Handle Category Filter
    if category_slug:
        selected_category = BlogCategory.objects.filter(slug=category_slug).first()
        if selected_category:
            posts_queryset = posts_queryset.filter(category=selected_category)

    # 3. Handle Search Query
    if query:
        posts_queryset = posts_queryset.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(excerpt__icontains=query)
        ).distinct()

    # 4. Handle Pagination (6 posts per page)
    paginator = Paginator(posts_queryset, 6)
    page_number = request.GET.get('page')
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    # 5. Fetch active categories for sidebar/filter
    categories = BlogCategory.objects.filter(status='ACTIVE').annotate(
        blog_count=Count('blog_posts', filter=Q(blog_posts__status='PUBLISHED'))
    ).order_by('name')

    # 6. Context data
    context = {
        'page_obj': page_obj,
        'query': query,
        'category_slug': category_slug,
        'selected_category': selected_category,
        'categories': categories,
        'total_count': posts_queryset.count(),
    }
    return render(request, "website/blog/list.html", context)


def blog_detail(request, slug):
    """
    Renders the detail page of a single blog post.
    Increments views_count on visit.
    """
    # Authorization checks: Staff can view drafts, public users can only see published posts.
    if request.user.is_staff:
        post = get_object_or_404(BlogPost.objects.select_related('category', 'author'), slug=slug)
    else:
        post = get_object_or_404(BlogPost.objects.select_related('category', 'author'), slug=slug, status='PUBLISHED')

    # WHY this exists: We increment the view count atomically using a Django F() expression.
    BlogPost.objects.filter(pk=post.pk).update(views_count=models.F('views_count') + 1)
    post.refresh_from_db()

    # Get recent posts for the sidebar (excluding the current one)
    recent_posts = BlogPost.objects.filter(status='PUBLISHED').exclude(pk=post.pk).select_related('category')[:3]

    # Fetch active categories for sidebar
    categories = BlogCategory.objects.filter(status='ACTIVE').annotate(
        blog_count=Count('blog_posts', filter=Q(blog_posts__status='PUBLISHED'))
    ).order_by('name')

    context = {
        'post': post,
        'recent_posts': recent_posts,
        'categories': categories,
    }
    return render(request, "website/blog/detail.html", context)


def blog_redirect(request, slug):
    """
    SEO 301 Permanent Redirect from legacy /blog/<slug>/ to top-level /<slug>/.
    Preserves existing backlinks and search engine rankings.
    """
    return redirect('blog_detail', slug=slug, permanent=True)



@login_required
def blog_create(request):
    """
    Form view for creating a new blog post. Restricted to staff users.
    """
    if not request.user.is_staff:
        return redirect('blog_list')

    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('blog_detail', slug=post.slug)
    else:
        form = BlogPostForm()

    context = {
        'form': form,
        'action': 'Create',
    }
    return render(request, 'website/blog/form.html', context)


@login_required
def blog_update(request, slug):
    """
    Form view for editing an existing blog post. Restricted to staff users.
    """
    if not request.user.is_staff:
        return redirect('blog_list')

    post = get_object_or_404(BlogPost, slug=slug)

    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            post = form.save()
            return redirect('blog_detail', slug=post.slug)
    else:
        form = BlogPostForm(instance=post)

    context = {
        'form': form,
        'action': 'Update',
        'post': post,
    }
    return render(request, 'website/blog/form.html', context)


@login_required
def blog_delete(request, slug):
    """
    Confirmation view for deleting an existing blog post. Restricted to staff users.
    """
    if not request.user.is_staff:
        return redirect('blog_list')

    post = get_object_or_404(BlogPost, slug=slug)

    if request.method == 'POST':
        post.delete()
        return redirect('blog_list')

    context = {
        'post': post,
    }
    return render(request, 'website/blog/delete_confirm.html', context)

