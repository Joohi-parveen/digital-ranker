from django.urls import path
from website import views

urlpatterns = [
    path("", views.case_study_list, name="case_study_list"),
    path("<slug:slug>/", views.case_study_detail, name="case_study_detail"),
]
