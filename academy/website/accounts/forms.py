from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import int_to_base36
from django.conf import settings
from django.template.loader import render_to_string

from academy.apps.accounts.models import User, Profile
from academy.apps.students.models import Student
from academy.apps.surveys.model import Survey
from academy.core.validators import validate_email, validate_mobile_phone, validate_username

from post_office import mail


class CustomAuthenticationForm(AuthenticationForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Username'
        self.fields['username'].widget = forms.TextInput(attrs={'placeholder': 'Email atau Username'})
        self.fields['password'].widget = forms.PasswordInput(attrs={'placeholder': 'Kata Sandi'})


class SignupForm(UserCreationForm):
    email = forms.EmailField(max_length=200)

    class Meta:
        model = User
        fields = ('email', 'username', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Username'
        self.fields['username'].validators = [validate_username]

    def save(self, *args, **kwargs):
        user = super().save(commit=False)
        user.is_active = False
        user.role = User.ROLE.student
        user.save()
        user.notification_register()

        return user


class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=70, label='Nama Depan')
    last_name = forms.CharField(max_length=70, required=False, label='Nama Belakang')
    phone_number = forms.CharField(max_length=16, validators=[validate_mobile_phone],
                                   label='Nomor Ponsel')

    class Meta:
        model = Profile
        fields = ('first_name', 'last_name', 'phone_number', 'linkedin', 'git_repo',
                  'blog', 'youtube', 'facebook', 'instagram', 'twitter', 'telegram_id')
        help_texts = {
            'git_repo': ('url akun github/gitlab/bitbucket dll'),
            'blog': ('url blog atau portfolio'),
            'youtube': ('url kanal youtube'),
            'facebook': ('contoh: "https://www.facebook.com/namaanda"'),
            'linkedin': ('contoh: "https://www.linkedin.com/in/namaanda/"'),
            'instagram': ('username Instagram'),
            'twitter': ('username Twitter tanpa "@"'),
            'telegram_id': ('contoh "@namaanda"'),
        }

    def clean_telegram_id(self):
        telegram_id = self.cleaned_data['telegram_id']
        if not telegram_id:
            return telegram_id

        if telegram_id[0] != '@':
            raise forms.ValidationError("Awal ID harus menggunakan karakter '@'")
        return telegram_id

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


class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(validators=[validate_email], label='',
                             widget=forms.TextInput(attrs={'placeholder': 'Email anda'}),
                             help_text='Kami akan mengirim email untuk mengatur ulang kata sandi Anda')

    # The link to reset your password will be sent to your email
    def clean_email(self):
        email = self.cleaned_data['email']

        user = User.objects.filter(email=email).first()
        if not user:
            raise forms.ValidationError("Email tidak terdaftar")

        return user

    def send_email(self, user):
        data = {
            'token': default_token_generator.make_token(user),
            'uid': int_to_base36(user.id),
            'host': settings.HOST,
            'user': user,
            'email_title': 'Lupa kata sandi'
        }

        mail.send(
            [user.email],
            settings.DEFAULT_FROM_EMAIL,
            subject='Lupa Kata Sandi',
            context=data,
            html_message=render_to_string('emails/forgot_password.html', context=data)
        )


class SurveyForm(forms.ModelForm):
    working_status = forms.ChoiceField(choices=Survey.WORKING_STATUS_CHOICES, label='Status pekerjaan saat ini:',
                                       widget=forms.RadioSelect)
    working_status_other = forms.CharField(label='Jawaban anda:', required=False)
    graduate_channeled = forms.ChoiceField(choices=Survey.TRUE_FALSE_CHOICES,
                                           label='Apabila anda telah lulus dari kelas nolsatu, apakah bersedia untuk disalurkan',
                                           widget=forms.RadioSelect)
    graduate_channeled_when = forms.ChoiceField(choices=Survey.GRADUATE_CHANNELED_TIME_CHOICES,
                                                label='Apabila bersedia untuk disalurkan, kapan waktu yang diinginkan',
                                                widget=forms.RadioSelect)
    graduate_channeled_when_other = forms.CharField(label='Jawaban anda:', required=False)

    class Meta:
        model = Survey
        exclude = ['user']

    def save(self, user, *args, **kwargs):
        survey = super().save(commit=False)
        survey.user = user
        survey.save()

        return survey
