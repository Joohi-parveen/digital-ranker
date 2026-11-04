from django import forms
from django.core.exceptions import ValidationError
from django.utils.text import slugify
import re
from django.utils.html import strip_tags
from website.models import BlogPost, BlogCategory, ContactMessage, Service, CaseStudy

RESERVED_ROOT_SLUGS = {
    'admin', 'dashboard', 'blog', 'blogs', 'about', 'contact', 'services', 
    'service', 'team', 'media', 'static', 'api', 'login', 'logout', 
    'categories', 'category', 'leads', 'seo', 'thank-you', 'thank_you'
}

class BlogCategoryForm(forms.ModelForm):
    """
    Form for creating and updating blog categories in the CMS.
    """
    class Meta:
        model = BlogCategory
        fields = ['name', 'slug', 'description', 'status']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Travel & Tourism'}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Leave blank to auto-generate'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Brief description of this category...'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise ValidationError("Category name is required.")
        qs = BlogCategory.objects.filter(name__iexact=name)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError(f"A category with the name '{name}' already exists.")
        return name

    def clean_slug(self):
        slug = self.cleaned_data.get('slug', '').strip()
        if slug:
            slug = slugify(slug)
            qs = BlogCategory.objects.filter(slug=slug)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(f"A category with the slug '{slug}' already exists.")
        return slug


def sanitize_blog_html(html_content):
    """
    Sanitize HTML to allow rich formatting while stripping dangerous scripts,
    event handlers, and unsafe protocols. Allows application/ld+json for Schema.
    """
    if not html_content:
        return ""
    
    # Save valid JSON-LD scripts to prevent them from being stripped
    placeholder = "___JSON_LD_SCRIPT_PLACEHOLDER___"
    scripts = []
    
    def save_script(match):
        scripts.append(match.group(0))
        return f"{placeholder}{len(scripts)-1}___"
        
    cleaned = re.sub(r'(?i)<script\s+type=[\'"]application/ld\+json[\'"][^>]*>.*?</script>', save_script, html_content, flags=re.DOTALL)
    
    # Remove all other script and style tags along with their inner contents
    cleaned = re.sub(r'<script\b[^>]*>.*?</script>', '', cleaned, flags=re.IGNORECASE | re.DOTALL)
    cleaned = re.sub(r'<style\b[^>]*>.*?</style>', '', cleaned, flags=re.IGNORECASE | re.DOTALL)
    cleaned = re.sub(r'<\/?(?:applet|embed|object|base|meta|link|frame|frameset)\b[^>]*>', '', cleaned, flags=re.IGNORECASE)
    
    # Strip javascript: and vbscript: URLs
    cleaned = re.sub(r'''(?i)(href|src)\s*=\s*(['"])\s*(?:javascript|vbscript):.*?\2''', r'\1="#"', cleaned)
    
    # Strip all on* event handler attributes (like onload, onerror, onclick, onmouseover, etc.)
    cleaned = re.sub(r'''(?i)\s+on[a-z]+\s*=\s*(['"]).*?\1''', '', cleaned)
    cleaned = re.sub(r'''(?i)\s+on[a-z]+\s*=\s*[^"'\s>]+''', '', cleaned)
    
    # Restore valid JSON-LD scripts
    for i, script in enumerate(scripts):
        cleaned = cleaned.replace(f"{placeholder}{i}___", script)
    
    return cleaned.strip()


class BlogPostForm(forms.ModelForm):
    """
    Form for creating and updating blog posts.
    """
    class Meta:
        model = BlogPost
        fields = [
            'title', 'slug', 'category', 'content', 'excerpt', 'featured_image', 
            'status', 'is_featured', 'meta_title', 'meta_description', 'meta_keywords',
            'schema_markup', 'faq_heading'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter blog title'}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Leave blank to auto-generate'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 14, 'placeholder': 'Write your content here...', 'id': 'id_content'}),
            'excerpt': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter brief summary for list views'}),
            'featured_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'meta_title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'SEO Title'}),
            'meta_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'SEO Meta Description (max 160 characters)'}),
            'meta_keywords': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'SEO Keywords, separated by commas'}),
            'schema_markup': forms.Textarea(attrs={'class': 'form-control font-monospace', 'rows': 4, 'placeholder': '{\n  "@context": "https://schema.org",\n  "@type": "Article"\n}'}),
            'faq_heading': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Frequently Asked Questions'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = BlogCategory.objects.all().order_by('name')
        self.fields['category'].empty_label = "--- Select Category ---"
        self.fields['category'].required = True

    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        if not title:
            raise ValidationError("Blog title is required.")
        return title

    def clean_content(self):
        content = self.cleaned_data.get('content', '').strip()
        sanitized = sanitize_blog_html(content)
        # Check if content is actually empty or just empty html tags like <p><br></p> or <p>&nbsp;</p>
        stripped = re.sub(r'<[^>]*>', '', sanitized).replace('&nbsp;', '').strip()
        has_media_or_structure = bool(re.search(r'<img\b|<table\b|<hr\b|<iframe\b', sanitized, re.IGNORECASE))
        if not sanitized or (not stripped and not has_media_or_structure):
            raise ValidationError("Body content is required and cannot be empty.")
        return sanitized

    def clean_slug(self):
        slug = self.cleaned_data.get('slug', '').strip()
        title = self.cleaned_data.get('title', '').strip()
        
        if not slug and title:
            slug = slugify(title, allow_unicode=True)
        elif slug:
            slug = slugify(slug, allow_unicode=True)
            
        if slug:
            qs = BlogPost.objects.filter(slug=slug)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(f"A blog post with the slug '{slug}' already exists.")
        return slug

    def clean_meta_description(self):
        meta_description = self.cleaned_data.get('meta_description', '').strip()
        if meta_description and len(meta_description) > 160:
            raise ValidationError("Meta description cannot exceed 160 characters.")
        return meta_description

    def clean_schema_markup(self):
        schema = self.cleaned_data.get('schema_markup', '').strip()
        if not schema:
            return schema
            
        import json
        
        # Strip script tags if user pasted the full tag
        if schema.lower().startswith('<script') and schema.lower().endswith('</script>'):
            # Extract content between tags
            import re
            match = re.search(r'<script[^>]*>(.*?)</script>', schema, re.DOTALL | re.IGNORECASE)
            if match:
                schema = match.group(1).strip()
        
        try:
            # Validate it's valid JSON
            json.loads(schema)
        except json.JSONDecodeError:
            raise ValidationError("Invalid JSON format. Please provide valid JSON or JSON-LD.")
            
        return schema


class ServiceForm(forms.ModelForm):
    """
    Form for creating and editing Service CMS pages with root-level SEO URLs.
    """
    class Meta:
        model = Service
        fields = [
            'title', 'slug', 'status',
            'hero_heading', 'hero_description', 'hero_cta_text', 'hero_cta_url', 'hero_banner_image',
            'content',
            'meta_title', 'meta_description', 'meta_keywords', 'robots_meta', 'canonical_url',
            'og_title', 'og_description', 'og_image'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Answer Engine Optimization'}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. answer-engine-optimization (leave blank to auto-generate)'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'hero_heading': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Build Lasting AI Visibility with AI SEO Agency in Delhi'}),
            'hero_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter banner description paragraph...', 'id': 'id_hero_description'}),
            'hero_cta_text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Request AI Proposal'}),
            'hero_cta_url': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. /contact/ (leave blank for default contact page)'}),
            'hero_banner_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 16, 'placeholder': 'Write service content or HTML...', 'id': 'id_content'}),
            'meta_title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'SEO Title (defaults to Service Title)'}),
            'meta_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'SEO Meta Description (150-160 characters recommended)'}),
            'meta_keywords': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'SEO Keywords, separated by commas'}),
            'robots_meta': forms.Select(attrs={'class': 'form-select'}),
            'canonical_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://aidigitalranker.com/your-service-slug/'}),
            'og_title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Open Graph Social Title'}),
            'og_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Open Graph Social Description'}),
            'og_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk and not self.initial.get('robots_meta'):
            self.initial['robots_meta'] = 'index, follow'

    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        if not title:
            raise ValidationError("Service title is required.")
        return title

    def clean_slug(self):
        slug = self.cleaned_data.get('slug', '').strip()
        title = self.cleaned_data.get('title', '').strip()
        if not slug and title:
            slug = slugify(title)
        elif slug:
            slug = slugify(slug)

        if not slug:
            raise ValidationError("A valid URL slug is required.")

        # 1. Collision check against reserved root-level URLs
        if slug.lower() in RESERVED_ROOT_SLUGS:
            raise ValidationError(f"The slug '{slug}' is reserved for system pages. Please choose a different slug.")

        # 2. Uniqueness check against other Service instances
        qs = Service.objects.filter(slug=slug)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError(f"A service with the slug '{slug}' already exists.")

        # 3. Collision check against BlogPosts
        if BlogPost.objects.filter(slug=slug).exists():
            raise ValidationError(f"A blog post with the root URL slug '{slug}' already exists. Please choose a unique slug.")

        return slug

    def clean_hero_description(self):
        desc = self.cleaned_data.get('hero_description', '').strip()
        if desc:
            return sanitize_blog_html(desc)
        return desc

    def clean_content(self):
        content = self.cleaned_data.get('content', '').strip()
        sanitized = sanitize_blog_html(content)
        stripped = re.sub(r'<[^>]*>', '', sanitized).replace('&nbsp;', '').strip()
        has_media_or_structure = bool(re.search(r'<img\b|<table\b|<hr\b|<iframe\b|<section\b|<div\b', sanitized, re.IGNORECASE))
        if not sanitized or (not stripped and not has_media_or_structure):
            raise ValidationError("Service body content is required and cannot be empty.")
        return sanitized

    def clean_meta_description(self):
        meta_description = self.cleaned_data.get('meta_description', '').strip()
        if meta_description and len(meta_description) > 300:
            raise ValidationError("Meta description is too long (max 300 characters).")
        return meta_description


class ContactForm(forms.ModelForm):
    """
    Form to handle validation and cleaning of frontend contact inquiry submissions.
    """
    phone = forms.CharField(required=False)
    subject = forms.CharField(required=False)
    message = forms.CharField(required=False, widget=forms.Textarea)

    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone', 'subject', 'message']

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        name = strip_tags(name)
        if not name:
            raise ValidationError("Name is required.")
        if len(name) > 100:
            raise ValidationError("Name cannot exceed 100 characters.")
        return name

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip()
        email = strip_tags(email)
        if not email:
            raise ValidationError("Email is required.")
        if len(email) > 254:
            raise ValidationError("Email cannot exceed 254 characters.")
        return email

    def clean_subject(self):
        subject = self.cleaned_data.get('subject', '').strip()
        subject = strip_tags(subject)
        if len(subject) > 200:
            raise ValidationError("Subject cannot exceed 200 characters.")
        return subject if subject else "General Inquiry"

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        phone = strip_tags(phone)
        if len(phone) > 20:
            raise ValidationError("Phone cannot exceed 20 characters.")
        return phone

    def clean_message(self):
        message = self.cleaned_data.get('message', '').strip()
        message = strip_tags(message)
        if len(message) > 2000:
            raise ValidationError("Message cannot exceed 2000 characters.")
        return message


class CaseStudyForm(forms.ModelForm):
    """
    Form for creating and updating case studies.
    """
    class Meta:
        model = CaseStudy
        fields = [
            'title', 'slug', 'client', 'content', 'featured_image', 
            'status', 'is_featured', 'meta_title', 'meta_description', 'meta_keywords',
            'schema_markup', 'faq_heading'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter case study title'}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Leave blank to auto-generate'}),
            'client': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Acme Corp or Healthcare Industry'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 10, 'placeholder': 'Additional detailed content (optional)...', 'id': 'id_content'}),
            'featured_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'meta_title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'SEO Title'}),
            'meta_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'SEO Meta Description (max 160 characters)'}),
            'meta_keywords': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'SEO Keywords, separated by commas'}),
            'schema_markup': forms.Textarea(attrs={'class': 'form-control font-monospace', 'rows': 4, 'placeholder': '{\n  "@context": "https://schema.org",\n  "@type": "Article"\n}'}),
            'faq_heading': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Frequently Asked Questions'}),
        }

    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        if not title:
            raise ValidationError("Case Study title is required.")
        return title



    def clean_content(self):
        content = self.cleaned_data.get('content', '').strip()
        if content:
            return sanitize_blog_html(content)
        return content

    def clean_slug(self):
        slug = self.cleaned_data.get('slug', '').strip()
        title = self.cleaned_data.get('title', '').strip()
        
        if not slug and title:
            slug = slugify(title, allow_unicode=True)
        elif slug:
            slug = slugify(slug, allow_unicode=True)
            
        if slug:
            qs = CaseStudy.objects.filter(slug=slug)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(f"A case study with the slug '{slug}' already exists.")
        return slug

    def clean_meta_description(self):
        meta_description = self.cleaned_data.get('meta_description', '').strip()
        if meta_description and len(meta_description) > 160:
            raise ValidationError("Meta description cannot exceed 160 characters.")
        return meta_description

    def clean_schema_markup(self):
        schema = self.cleaned_data.get('schema_markup', '').strip()
        if not schema:
            return schema
            
        import json
        
        if schema.lower().startswith('<script') and schema.lower().endswith('</script>'):
            import re
            match = re.search(r'<script[^>]*>(.*?)</script>', schema, re.DOTALL | re.IGNORECASE)
            if match:
                schema = match.group(1).strip()
        
        try:
            json.loads(schema)
        except json.JSONDecodeError:
            raise ValidationError("Invalid JSON format. Please provide valid JSON or JSON-LD.")
            
        return schema

from django.forms import inlineformset_factory
from .models.blog import BlogFAQ

class BlogFAQForm(forms.ModelForm):
    class Meta:
        model = BlogFAQ
        fields = ['question', 'answer', 'order']
        widgets = {
            'question': forms.TextInput(attrs={'class': 'form-control faq-question', 'placeholder': 'Enter question'}),
            'answer': forms.Textarea(attrs={'class': 'form-control faq-answer', 'rows': 3, 'placeholder': 'Enter answer'}),
            'order': forms.NumberInput(attrs={'class': 'form-control faq-order', 'style': 'width: 80px;'}),
        }

BlogFAQFormSet = inlineformset_factory(
    BlogPost, 
    BlogFAQ, 
    form=BlogFAQForm, 
    extra=1, 
    can_delete=True
)

from .models.case_study import CaseStudyFAQ

class CaseStudyFAQForm(forms.ModelForm):
    class Meta:
        model = CaseStudyFAQ
        fields = ['question', 'answer', 'order']
        widgets = {
            'question': forms.TextInput(attrs={'class': 'form-control faq-question', 'placeholder': 'Enter question'}),
            'answer': forms.Textarea(attrs={'class': 'form-control faq-answer', 'rows': 3, 'placeholder': 'Enter answer'}),
            'order': forms.NumberInput(attrs={'class': 'form-control faq-order', 'style': 'width: 80px;'}),
        }

CaseStudyFAQFormSet = inlineformset_factory(
    CaseStudy, 
    CaseStudyFAQ, 
    form=CaseStudyFAQForm, 
    extra=1, 
    can_delete=True
)
