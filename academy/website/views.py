from django.shortcuts import render, redirect, get_object_or_404
from django.template import loader
from django.http import JsonResponse

from datetime import datetime, timedelta

from academy.apps.accounts.models import Instructor
from academy.apps.accounts.models import User
from academy.apps.students.models import Student
from academy.apps.graduates.models import Graduate

from .forms import CertificateVerifyForm

def index(request):
    context = {
        'title': 'Home',
        'instructors': Instructor.objects.order_by('order'),
        'pendaftar': User.objects.exclude(is_superuser=True).exclude(is_staff=True).count(),
        'peserta': Student.objects.filter(status = Student.STATUS.participants).count(),
        'lulus': Student.objects.filter(status = Student.STATUS.graduate).count()
    }
    return render(request, 'website/home.html', context)


def faq(request):
    context = {
        'title': 'Tilil (Q&A)'
    }
    return render(request, 'website/faq.html', context)


def certificate_verify(request):
    form = CertificateVerifyForm(request.POST or None)
    result = None
    valid_date = None

    if form.is_valid():
        student = form.verification()
        if student:
            result = student
            valid_date = student.created + timedelta(days=1095)
        else:
            result = ""

    context = {
        'title': 'Verifikasi Sertifikat',
        'form': form,
        'result': result,
        'valid_date': valid_date
    }

    if request.is_ajax():
        html = loader.render_to_string('website/result-verify.html', context)
        return JsonResponse({'html': html})
    return render(request, 'website/cert-verify.html', context)


def home(request):
    context = {
        'title': 'Home 2'
    }
    return render(request, 'website/home2.html', context)


def error_404(request):
    return render(request, '404.html', {})


def error_500(request):
    return render(request, '500.html', {})