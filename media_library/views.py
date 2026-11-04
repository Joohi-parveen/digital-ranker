from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from dashboard.views import staff_required
from media_library.models import MediaAsset
from media_library.forms import MediaUploadForm

@staff_required
def media_list(request):
    """
    Renders the Media Library image grid.
    Supports filtering by filename and paginating results.
    Also handles POST requests for file uploads.
    """
    query = request.GET.get('q', '').strip()
    assets = MediaAsset.objects.all()

    if query:
        assets = assets.filter(original_filename__icontains=query)

    # Paginate (12 images per page as specified in requirements)
    paginator = Paginator(assets, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Handle file upload POST requests
    if request.method == 'POST':
        upload_form = MediaUploadForm(request.POST, request.FILES)
        if upload_form.is_valid():
            asset = upload_form.save()
            messages.success(request, f"File '{asset.original_filename}' uploaded successfully!")
            return redirect('media_list')
        else:
            messages.error(request, "Failed to upload file. Please check form validation errors below.")
    else:
        upload_form = MediaUploadForm()

    context = {
        'page_obj': page_obj,
        'query': query,
        'upload_form': upload_form,
        'active_tab': 'media',
    }
    return render(request, 'media_library/media_list.html', context)


@staff_required
@require_POST
def media_delete(request, pk):
    """
    Deletes the selected MediaAsset and removes the file from disk.
    Only allows POST requests for security.
    """
    asset = get_object_or_404(MediaAsset, pk=pk)
    filename = asset.original_filename
    asset.delete()
    messages.success(request, f"File '{filename}' deleted successfully.")
    return redirect('media_list')
