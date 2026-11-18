from django.urls import path

from . import views

app_name = 'applicants'

urlpatterns = [
    path('', views.ApplicantListView.as_view(), name='list'),
    path('applications/', views.ApplicantListView.as_view(application_view=True), name='applications'),
    path('create/', views.applicant_create, name='create'),
    path('create/restart/', views.applicant_restart, name='restart'),
    path('<int:pk>/assign/', views.assign_underwriter, name='assign'),
    path('<int:pk>/', views.ApplicantDetailView.as_view(), name='detail'),
]
