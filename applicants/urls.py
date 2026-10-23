from django.urls import path

from . import views

app_name = 'applicants'

urlpatterns = [
    path('', views.ApplicantListView.as_view(), name='list'),
    path('create/', views.applicant_create, name='create'),
    path('<int:pk>/', views.ApplicantDetailView.as_view(), name='detail'),
]
