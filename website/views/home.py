from django.shortcuts import render, redirect
from django.contrib import messages
from website.forms import ContactForm
from website.models import BlogPost, Service
from website.utils.ip import get_client_ip
from website.utils.mail import send_lead_emails
from website.utils.spam_check import is_ip_blocked
from django.template.loader import get_template
from django.template import TemplateDoesNotExist
from django.http import Http404

from django.core.cache import cache

def home(request):
    """
    Renders the main landing page of the website.
    Uses optimized caching and select_related database query for faster load times.
    """
    latest_posts = cache.get('homepage_latest_posts')
    if not latest_posts:
        latest_posts = list(
            BlogPost.objects.select_related('category', 'author')
            .filter(status='PUBLISHED')
            .order_by('-created_at')[:3]
        )
        # Cache the results in memory for 1 hour (3600 seconds)
        cache.set('homepage_latest_posts', latest_posts, 3600)
        
    return render(request, "website/index.html", {"latest_posts": latest_posts})

def dynamic_page_detail(request, slug):
    """
    Unified dynamic resolver for root-level SEO URLs (/slug/):
    1. Checks if a database-driven Service exists with this slug.
    2. If not, checks if a BlogPost exists with this slug.
    3. If neither exists, checks if a legacy static template exists in website/services/{slug}.html.
    4. If none found, raises Http404.
    """
    # 1. Check if a Service exists
    service_qs = Service.objects.all()
    if not request.user.is_staff:
        service_qs = service_qs.filter(status='PUBLISHED')

    service = service_qs.filter(slug=slug).first()
    if service:
        if request.method == "POST":
            form = ContactForm(request.POST)
            if form.is_valid():
                client_ip = get_client_ip(request)
                if is_ip_blocked(client_ip):
                    messages.error(request, "Unable to process your submission at this time. Please try again later.")
                    return redirect('service_detail', slug=slug)

                lead = form.save(commit=False)
                lead.ip_address = client_ip
                lead.save()
                send_lead_emails(lead)
                return redirect('thank_you')
            else:
                messages.error(request, "Please fill in all the required fields with valid details.")
        return render(request, "website/services/service-detail.html", {"service": service})

    # 2. Check if a BlogPost exists
    blog_qs = BlogPost.objects.select_related('category', 'author')
    if not request.user.is_staff:
        blog_qs = blog_qs.filter(status='PUBLISHED')
        
    post = blog_qs.filter(slug=slug).first()
    if post:
        # Legacy URLs hit this route. 301 redirect to the correct /blog/<slug>/ URL.
        return redirect('blog_detail', slug=post.slug, permanent=True)

    # 3. Check if a legacy static service template exists (excluding the generic service-detail)
    if slug != "service-detail":
        template_name = f"website/services/{slug}.html"
        try:
            get_template(template_name)
            return render(request, template_name)
        except TemplateDoesNotExist:
            pass

    # 4. Neither found
    raise Http404("Page not found.")

def service_detail(request, slug):
    """
    Alias to dynamic_page_detail for backwards compatibility and named URL routing.
    """
    return dynamic_page_detail(request, slug)

def about(request):
    """
    Renders the about us page.
    """
    return render(request, "website/about.html")

def services(request):
    """
    Renders the services page.
    """
    return render(request, "website/services.html")

def contact(request):
    """
    Renders the contact page and handles form submissions.
    Redirects to the Thank You page on success.
    """
    if request.method == "POST":
        form = ContactForm(request.POST)
        next_url = request.POST.get('next')
        if form.is_valid():
            client_ip = get_client_ip(request)
            if is_ip_blocked(client_ip):
                messages.error(request, "Unable to process your submission at this time. Please try again later.")
                if next_url:
                    return redirect(next_url)
                return redirect('contact')

            lead = form.save(commit=False)
            lead.ip_address = client_ip
            lead.save()
            send_lead_emails(lead)
            return redirect('thank_you')
        else:
            messages.error(request, "Please fill in all the required fields with valid details.")
            if next_url:
                return redirect(next_url)

    return render(request, "website/contact.html")

def thank_you(request):
    """
    Renders the dedicated Thank You confirmation page after a successful lead submission.
    """
    return render(request, "website/thank-you.html")





