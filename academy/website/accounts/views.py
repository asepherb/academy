from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.http import base36_to_int
from django.contrib.auth.tokens import default_token_generator
from django.http import Http404
from django.contrib.auth.forms import SetPasswordForm

from academy.apps.accounts.models import User
from academy.apps.students.models import Training, Student
from .forms import CustomAuthenticationForm, SignupForm, ProfileForm, StudentForm, ForgotPasswordForm, SurveyForm


@login_required
def index(request):
    if not hasattr(request.user, 'survey'):
        return redirect("website:accounts:survey")

    user = request.user
    training = Training.objects.filter(is_active=True).order_by('batch').last()

    if hasattr(user, 'profile'):
        student = request.user.get_student()
        graduate = None

        if hasattr(student, 'graduate'):
            graduate = student.graduate
            graduate.generate_certificate_file()

        context = {
            'title': 'Dasbor',
            'student': student,
            'graduate': graduate
        }
        return render(request, 'dashboard/index.html', context)

    form = ProfileForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.save(user)
        form_student = StudentForm(data={'user': user.id, 'training': training.id})
        if form_student.is_valid():
            form_student.save()

        return redirect("website:accounts:index")

    context = {
        'title': 'Lengkapi Profil Anda',
        'form': form
    }
    return render(request, 'accounts/index.html', context)


def login_view(request):
    if request.user.is_authenticated():
        return redirect('website:accounts:index')

    form = CustomAuthenticationForm(request, data=request.POST or None)
    if form.is_valid():
        user = form.get_user()
        login(request, user)

        next = request.GET.get('next') or None
        if next:
            return redirect(next)
        else:
            return redirect("website:accounts:index")

    context = {
        'form': form,
        'title': 'Masuk',
        'page': 'login'
    }
    return render(request, 'accounts/form.html', context)


def logout_view(request):
    logout(request)
    return redirect("website:index")


def sign_up(request):
    if request.user.is_authenticated():
        return redirect('website:accounts:index')

    form = SignupForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Tolong cek email Anda untuk mengaktifkan akun')
        return redirect('website:accounts:sign_up')

    context = {
        'form': form,
        'title': 'Daftar',
        'page': 'sign-up'
    }
    return render(request, 'accounts/form.html', context)


def active_account(request, uidb36, token):
    try:
        uid_int = base36_to_int(uidb36)
    except ValueError:
        raise Http404

    user = get_object_or_404(User, id=uid_int)
    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save(update_fields=['is_active'])
        login(request, user)
        messages.success(request, 'Selamat, akun Anda sudah aktif')
    else:
        messages.warning(request, 'Maaf, ada masalah dengan aktivasi akun')

    return redirect("website:accounts:index")


def profile(request):
    user = request.user
    student = request.user.get_student()
    graduate = None
    survey = None

    if hasattr(student, 'graduate'):
        graduate = student.graduate
        graduate.generate_certificate_file()

    if hasattr(user, 'survey'):
        survey = user.survey

    context = {
        'title': 'Dashboard',
        'user': user,
        'student': student,
        'graduate': graduate,
        'survey': survey
    }
    return render(request, 'dashboard/profile.html', context)


@login_required
def edit_profile(request):
    user = request.user

    initial = {
        'first_name': user.first_name,
        'last_name': user.last_name,
        'phone_number': user.phone,
        'avatar': user.profile.avatar,
        'birthday': user.profile.birthday,
        'gender': user.profile.gender,
        'address': user.profile.address,
        'linkedin': user.profile.linkedin,
        'git_repo': user.profile.git_repo,
        'blog': user.profile.blog,
        'facebook':user.profile.facebook,
        'youtube': user.profile.youtube,
        'twitter': user.profile.twitter,
        'instagram': user.profile.instagram
    }

    form = ProfileForm(request.POST or None, request.FILES or None,
                          initial=initial, instance=user.profile)
    if form.is_valid():
        form.save(user)
        messages.success(request, 'Profil berhasil diubah')
        return redirect("website:accounts:profile")

    context = {
        'title': 'Ubah Profil',
        'form': form
    }
    return render(request, 'dashboard/edit_profile.html', context)


def forgot_password(request):
    form = ForgotPasswordForm(request.POST or None)

    if form.is_valid():
        form.send_email(form.cleaned_data['email'])
        messages.success(request, 'Silahkan cek email untuk mengatur ulang kata sandi')
        return redirect('website:accounts:forgot_password')

    context = {
        'title': 'Lupa kata sandi',
        'form': form,
    }
    return render(request, 'accounts/form.html', context)


def reset_password(request, uidb36, token):

    try:
        uid_int = base36_to_int(uidb36)
    except ValueError:
        raise Http404

    user = get_object_or_404(User, id=uid_int)
    if user and default_token_generator.check_token(user, token):
        form = SetPasswordForm(user=user, data=request.POST or None)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Kata sandi baru anda berhasil disimpan')
            return redirect('website:accounts:login')
    else:
        messages.warning(request, 'Maaf, permintaan atur ulang kata sandi sudah'
                         'kadaluarsa. Silahkan coba lagi')
        return redirect('website:accounts:login')

    context = {
        'title': 'Atur Ulang',
        'form': form,
        'page': 'reset-password'
    }
    return render(request, 'accounts/form.html', context)


@login_required
def survey(request):
    if hasattr(request.user, 'survey'):
        return redirect("website:accounts:index")

    form = SurveyForm(data=request.POST or None)
    if form.is_valid():
        form.save(request.user)
        messages.success(request, 'Terima kasih telah mengisi survey')
        return redirect("website:accounts:index")

    context = {
        'title': 'Mohon isi data berikut',
        'form': form,
        'page': 'survey'
    }
    return render(request, 'accounts/survey-form.html', context)


@login_required
def edit_survey(request):
    if not hasattr(request.user, 'survey'):
        return redirect("website:accounts:index")

    survey = request.user.survey
    form = SurveyForm(data=request.POST or None, instance=survey)
    if form.is_valid():
        form.save(request.user)
        return redirect("website:accounts:profile")

    context = {
        'title': 'Data Pekerjaan',
        'form': form,
        'page': 'survey'
    }
    return render(request, 'accounts/survey-form.html', context)
