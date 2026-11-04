from django import forms
from django.contrib.auth.forms import AuthenticationForm

class DashboardLoginForm(AuthenticationForm):
    """
    Custom styled login form for the admin dashboard.
    """
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'class': 'form-control form-control-lg bg-white border border-light-subtle rounded-3 px-3 py-2',
                'placeholder': 'Enter your username',
                'id': 'username_field'
            }
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control form-control-lg bg-white border border-light-subtle rounded-3 px-3 py-2',
                'placeholder': 'Enter your password',
                'id': 'password_field'
            }
        )
    )


from website.models.seo import PageSEOSetting
from website.forms import BlogCategoryForm, BlogPostForm

class PageSEOSettingForm(forms.ModelForm):
    """
    Form to manage SEO Settings for a specific page.
    """
    class Meta:
        model = PageSEOSetting
        fields = [
            'site_title', 'meta_title', 'meta_description', 'meta_keywords',
            'canonical_url', 'robots_meta', 'og_title', 'og_description',
            'og_image', 'favicon'
        ]
        widgets = {
            'site_title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. AI Digital Ranker'}),
            'meta_title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Home - Lead SEO Solutions'}),
            'meta_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Write a compelling meta description here...'}),
            'meta_keywords': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. generative search, seo, AI marketing'}),
            'canonical_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'e.g. https://aidigitalranker.com/'}),
            'robots_meta': forms.Select(attrs={'class': 'form-select'}),
            'og_title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Social sharing title'}),
            'og_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Social sharing description'}),
            'og_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'favicon': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


from website.models.blocked_ip import BlockedIP
from website.utils.ip import is_valid_ip


class BlockedIPForm(forms.ModelForm):
    """
    Form for adding and managing blocked IP addresses in the CMS.
    """
    class Meta:
        model = BlockedIP
        fields = ['ip_address', 'reason', 'expires_at', 'is_active']
        widgets = {
            'ip_address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 198.51.100.45 or 2001:db8::1'
            }),
            'reason': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Repeated spam inquiry bot, scam attempt...'
            }),
            'expires_at': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def clean_ip_address(self):
        ip = self.cleaned_data.get('ip_address', '').strip()
        if not ip:
            raise forms.ValidationError("IP address is required.")
        if not is_valid_ip(ip):
            raise forms.ValidationError("Enter a valid IPv4 or IPv6 address (e.g. 192.168.1.1 or 2001:db8::1).")

        qs = BlockedIP.objects.filter(ip_address=ip)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(f"The IP address '{ip}' is already in the blocklist.")
        return ip

