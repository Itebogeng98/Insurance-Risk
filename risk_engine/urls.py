from django.urls import path

from . import views

app_name = 'risk_engine'

urlpatterns = [
    path('models/kaggle/', views.kaggle_analysis, name='kaggle_analysis'),
    path('models/kaggle/sample.csv', views.kaggle_sample, name='kaggle_sample'),
    path('models/applicant-template.csv', views.applicant_training_template, name='applicant_training_template'),
    path('applicants/<int:applicant_id>/assess/', views.assess_applicant_view, name='assess'),
    path('models/', views.model_management, name='model_management'),
]
