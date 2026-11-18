from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, UserCreationForm

from config.form_utils import add_bootstrap_classes

from .models import UserProfile

User = get_user_model()


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(
        choices=(
            (UserProfile.Role.CUSTOMER, UserProfile.Role.CUSTOMER.label),
        ),
        initial=UserProfile.Role.CUSTOMER,
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'role', 'password1', 'password2')

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        add_bootstrap_classes(self)
        self.fields['username'].widget.attrs['placeholder'] = 'Choose a username'
        self.fields['email'].widget.attrs['placeholder'] = 'name@example.com'
        self.fields['password1'].widget.attrs['placeholder'] = 'Create a secure password'
        self.fields['password2'].widget.attrs['placeholder'] = 'Repeat your password'

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            user.profile.role = self.cleaned_data['role']
            user.profile.save(update_fields=['role'])
        return user


class StyledAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        add_bootstrap_classes(self)
        self.fields['username'].widget.attrs['placeholder'] = 'Username'
        self.fields['password'].widget.attrs['placeholder'] = 'Password'


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        add_bootstrap_classes(self)
        self.fields['first_name'].widget.attrs['placeholder'] = 'First name'
        self.fields['last_name'].widget.attrs['placeholder'] = 'Last name'
        self.fields['email'].widget.attrs['placeholder'] = 'name@example.com'
        for name in ('first_name', 'last_name', 'email'):
            self.fields[name].required = True
            self.fields[name].widget.attrs['required'] = True


class StyledPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        add_bootstrap_classes(self)
        self.fields['old_password'].widget.attrs['placeholder'] = 'Current password'
        self.fields['new_password1'].widget.attrs['placeholder'] = 'New password'
        self.fields['new_password2'].widget.attrs['placeholder'] = 'Confirm new password'
