from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from academy.apps.accounts.models import User, Profile
from academy.apps.students.models import Student
from academy.core.validators import validate_email, validate_mobile_phone


class CustomAuthenticationForm(AuthenticationForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget = forms.TextInput(attrs={'placeholder': 'Email atau Nama Pengguna'})
        self.fields['password'].widget = forms.PasswordInput(attrs={'placeholder': 'Kata Sandi'})


class SignupForm(UserCreationForm):
    email = forms.EmailField(max_length=200)

    class Meta:
        model = User
        fields = ('email', 'username', 'password1', 'password2')

    def save(self, *args, **kwargs):
        user = super().save(commit=False)
        user.is_active = False
        user.role = User.ROLE.student
        user.save()
        user.notification_register()

        return user


class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=70)
    last_name = forms.CharField(max_length=70, required=False)
    phone_number = forms.CharField(max_length=16, validators=[validate_mobile_phone])

    class Meta:
        model = Profile
        fields = ('first_name', 'last_name', 'phone_number', 'linkedin', 'git_repo',
                  'blog', 'youtube', 'facebook', 'instagram', 'twitter')
        help_texts = {
            'git_repo': ('url akun github/gitlab/bitbucket dll'),
            'blog': ('url blog atau portfolio'),
            'youtube': ('url kanal youtube'),
            'facebook': ('e.g. "https://www.facebook.com/yourname"'),
            'linkedin': ('e.g. "https://www.linkedin.com/in/yourname/"'),
            'instagram': ('Instagram username e.g. YourName'),
            'twitter': ('Twitter username without "@" e.g. YourName'),
        }

    def save(self, user, *args, **kwargs):
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone = self.cleaned_data['phone_number']
        user.save()

        profile = super().save(commit=False)
        profile.user = user
        profile.save()

        return profile


class StudentForm(forms.ModelForm):

    class Meta:
        model = Student
        fields = ('user', 'training')