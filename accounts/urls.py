from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from .forms import StyledPasswordChangeForm
from . import views

app_name = 'accounts'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.ProfileUpdateView.as_view(), name='profile'),
    path(
        'password/',
        auth_views.PasswordChangeView.as_view(
            form_class=StyledPasswordChangeForm,
            template_name='accounts/password_change.html',
            success_url=reverse_lazy('accounts:password_change_done'),
        ),
        name='password_change',
    ),
    path(
        'password/done/',
        auth_views.PasswordChangeDoneView.as_view(
            template_name='accounts/password_change_done.html',
        ),
        name='password_change_done',
    ),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.AccountLoginView.as_view(), name='login'),
    path('logout/', views.AccountLogoutView.as_view(), name='logout'),
    path('privacy/', views.LegalPageView.as_view(), {'page': 'privacy'}, name='privacy'),
    path('terms/', views.LegalPageView.as_view(), {'page': 'terms'}, name='terms'),
    path('paia/', views.LegalPageView.as_view(), {'page': 'paia'}, name='paia'),
]
