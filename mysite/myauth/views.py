from random import random

from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.contrib.auth.forms import BaseUserCreationForm
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import User
from django.contrib.auth.views import LogoutView
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.urls import reverse_lazy, reverse
from django.views import View
from django.views.generic import TemplateView, CreateView, ListView, DetailView, UpdateView
from django.utils.translation import gettext_lazy as _, ngettext
from django.views.decorators.cache import cache_page

from .models import Profile
from .forms import ProfileForm


class HelloView(View):
    welcome_message = _("welcome hello world")

    def get(self, request: HttpRequest) -> HttpResponse:
        items_str = request.GET.get("items") or 0
        items = int(items_str)
        products_line = ngettext(
            "one product",
            "{count} products",
            items,
        )
        products_line = products_line.format(count=items)
        return HttpResponse(
            f"<h1>{self.welcome_message}</h1>"
            f"\n<h2>{products_line}</h2>"
        )

class AboutMeView(TemplateView):
    template_name = "myauth/about-me.html"

class ProfileUpdateView(UserPassesTestMixin, UpdateView):
    model = Profile
    form_class = ProfileForm
    template_name = "myauth/profile_update.html"

    def test_func(self):
        profile = self.get_object()
        user = self.request.user
        return user.is_staff or profile.user == user

    def get_success_url(self):
        return reverse("myauth:about-me")


class UsersListView(ListView):
    template_name = "myauth/users-list.html"
    context_object_name = "users"
    queryset = User.objects.select_related("profile").all()


class UserDetailsView(DetailView):
    template_name = "myauth/user-details.html"
    model = User
    context_object_name = "user_obj"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_edit"] = (
            self.request.user.is_staff or
            self.object == self.request.user
        )
        return context

class RegisterView(CreateView):
    form_class = BaseUserCreationForm
    template_name = "myauth/register.html"
    success_url = reverse_lazy("myauth:about-me")

    def form_valid(self, form):
        response = super().form_valid(form)
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password1')
        user = authenticate(
            self.request,
            username=username,
            password=password,
        )
        login(request=self.request, user=user)
        return response


def login_view(request: HttpRequest) -> HttpResponse:
    if request.method == 'GET':
        if request.user.is_authenticated:
            return redirect('/admin/')
        return render(request, 'myauth/login.html')

    username = request.POST.get('username')
    password = request.POST.get('password')

    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        return redirect('/admin/')

    return render(request, 'myauth/login.html', {"error": "Invalid login credentials"})

class MyLogoutView(LogoutView):
    next_page = reverse_lazy('myauth:login')
    http_method_names = ['get', 'post', 'head', 'options']

    def get(self, request, *args, **kwargs):
        return render(request, 'myauth/logout_confirm.html')

    def post(self, request, *args, **kwargs):
        print(f"Пользователь {request.user} выходит из системы.")
        return super().post(request, *args, **kwargs)

@user_passes_test(lambda u: u.is_superuser)
def set_cookie_view(request: HttpRequest) -> HttpResponse:
    response = HttpResponse("Cookie set")
    response.set_cookie('fizz', 'buzz', max_age=3600)
    return response

@cache_page(60 * 2)
@login_required
def get_cookie_view(request: HttpRequest) -> HttpResponse:
    value = request.COOKIES.get('fizz', 'default value')
    return HttpResponse(f"Cookie value: {value!r} + {random()}")

@permission_required('myauth.view_profile', raise_exception=True)
def set_session_view(request: HttpRequest) -> HttpResponse:
    request.session["foobar"] = "spameggs"
    return HttpResponse("Session set")

@login_required
def get_session_view(request: HttpRequest) -> HttpResponse:
    value = request.session.get("foobar", "default value")
    return HttpResponse(f"Session value: {value!r}")

class FooBarView(View):
    def get(self, request: HttpRequest) -> JsonResponse:
        return JsonResponse({'foo': 'bar', 'spam': 'eggs'})