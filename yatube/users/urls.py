from django import views
from django.contrib.auth import views as viw
from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('signup/', views.SignUp.as_view(), name='signup'),
    path(
        'logout/',
        viw.LogoutView.as_view(template_name='users/logged_out.html'),
        name='logout'
    ),
    path(
        'login/',
        viw.LoginView.as_view(template_name='users/login.html'),
        name='login'
    ),
    path(
        'password_change/',
        viw.PasswordChangeView.as_view(
            template_name='users/password_change_form.html'
        ),
        name='password_change'
    ),
    path(
        'password_change/done/',
        views.password_change_done,
        name='password_change_done'
    ),
    path(
        'password_reset',
        viw.PasswordResetView.as_view(
            template_name='users/password_reset_form.html'
        ),
        name='password_reset'
    ),
    path(
        'password_reset/done/',
        views.password_reset_done,
        name='password_reset_done'
    ),
    path(
        'reset/<uidb64>/<token>/',
        viw.PasswordResetConfirmView.as_view(
            template_name='users/password_reset_confirm.html'
        )
    ),
    path(
        'reset/done/',
        viw.PasswordResetCompleteView.as_view(
            template_name='users/password_reset_complete.html'
        )
    ),

]
