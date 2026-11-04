from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import models
from django.db.models import Q
from website.models import CaseStudy

def case_study_list(request):
    """
    Renders a paginated list of published case studies.
    """
    if request.user.is_staff:
        case_studies_qs = CaseStudy.objects.all()
    else:
        case_studies_qs = CaseStudy.objects.filter(status='PUBLISHED')

    paginator = Paginator(case_studies_qs, 9) # 9 case studies per page
    page_number = request.GET.get('page')
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    context = {
        'page_obj': page_obj,
        'total_count': case_studies_qs.count(),
    }
    return render(request, "website/case_studies/list.html", context)


def case_study_detail(request, slug):
    """
    Renders the detail page of a single case study.
    Increments views_count on visit.
    """
    if request.user.is_staff:
        case_study = get_object_or_404(CaseStudy, slug=slug)
    else:
        case_study = get_object_or_404(CaseStudy, slug=slug, status='PUBLISHED')

    # Atomically increment views count
    CaseStudy.objects.filter(pk=case_study.pk).update(views_count=models.F('views_count') + 1)
    case_study.refresh_from_db()

    # Get recent case studies for sidebar/related section
    recent_case_studies = CaseStudy.objects.filter(status='PUBLISHED').exclude(pk=case_study.pk)[:3]

    context = {
        'case_study': case_study,
        'recent_case_studies': recent_case_studies,
    }
    return render(request, "website/case_studies/detail.html", context)
