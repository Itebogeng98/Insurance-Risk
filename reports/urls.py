from django.urls import path

from . import views

app_name = 'reports'

urlpatterns = [
    path('applicants/<int:applicant_id>/', views.underwriting_report, name='underwriting'),
    path('applicants/<int:applicant_id>/pdf/', views.underwriting_report_pdf, name='underwriting_pdf'),
]
