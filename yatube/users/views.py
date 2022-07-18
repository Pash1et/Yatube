from django.shortcuts import render
from django.views.generic import CreateView
from django.urls import reverse_lazy
from .forms import CreationForm


class SignUp(CreateView):
    form_class = CreationForm
    template_name = 'users/signup.html'
    success_url = reverse_lazy('posts:index')


def password_change_done(request):
    return render(request, 'users/password_change_done.html')


def password_reset_done(request):
    return render(request, 'users/password_reset_done.html')
