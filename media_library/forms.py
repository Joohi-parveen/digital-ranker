import os
from django import forms
from django.core.exceptions import ValidationError
from media_library.models import MediaAsset

class MediaUploadForm(forms.ModelForm):
    """
    Form for uploading new files to the Media Library.
    Validates file extensions to secure and restrict media formats.
    """
    class Meta:
        model = MediaAsset
        fields = ['file', 'alt_text']
        widgets = {
            'file': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': '.jpg,.jpeg,.png,.svg,.webp'
            }),
            'alt_text': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter alternative text for SEO/accessibility'
            }),
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            ext = os.path.splitext(file.name)[1].lower()
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.svg', '.webp']
            if ext not in allowed_extensions:
                raise ValidationError(
                    f"Unsupported file format '{ext}'. Allowed formats are: {', '.join(allowed_extensions)}."
                )
        return file
