from django.urls import path

from . import views

app_name = 'risk_engine'

urlpatterns = [
    path('models/applicant-template.csv', views.applicant_training_template, name='applicant_training_template'),
    path('applicants/<int:applicant_id>/assess/', views.assess_applicant_view, name='assess'),
    path('models/', views.model_management, name='model_management'),
]
