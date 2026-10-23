from django.contrib import admin
from django.urls import include, path

from accounts.views import home
from .health import health
from risk_engine import api

urlpatterns = [
    path('healthz/', health, name='health'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('applicants/', include('applicants.urls')),
    path('reports/', include('reports.urls')),
    path('risk/', include('risk_engine.urls')),
    path('api/v1/auth/register', api.api_register, name='api_register'),
    path('api/v1/auth/login', api.api_login, name='api_login'),
    path('api/v1/applicants', api.api_create_applicant, name='api_create_applicant'),
    path('api/v1/predict-risk', api.api_predict_risk, name='api_predict_risk'),
    path('api/v1/assessments/<int:assessment_id>', api.api_assessment_detail, name='api_assessment_detail'),
    path('api/v1/reports/<int:assessment_id>', api.api_report_pdf, name='api_report_pdf'),
    path('api/v1/datasets', api.api_upload_dataset, name='api_upload_dataset'),
    path('', home, name='landing'),
]
