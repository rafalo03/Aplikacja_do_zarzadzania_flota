from django.contrib import admin
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import views as auth_views
from django.urls import path, include
from django.shortcuts import render, redirect
from django.views.decorators.csrf import ensure_csrf_cookie
from pojazdy.models import Pojazd
from pojazdy.models import Polisa
from kontrahenci.models import Kontrahent

@ensure_csrf_cookie
def dashboard(request):
    context = {
        'liczba_pojazdow': Pojazd.objects.count(),
        'liczba_polis': Polisa.objects.count(),
        'liczba_kontrahentow': Kontrahent.objects.count(),
    }
    template = 'dashboard_view.html' if request.headers.get('HX-Request') else 'dashboard.html'
    return render(request, template, context)

def wyloguj_do_aplikacji(request):
    auth_logout(request)
    return redirect('login')

class LogowanieView(auth_views.LoginView):
    template_name = 'login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        if not self.request.POST.get('remember_me'):
            self.request.session.set_expiry(0)
        return super().form_valid(form)

urlpatterns = [
    path('admin/logout/', wyloguj_do_aplikacji),
    path('admin/', admin.site.urls),
    path('login/', LogowanieView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('', dashboard, name='dashboard'),
    path('', include('pojazdy.urls')),
    path('', include('administracja.urls')),
    path('', include('serwis.urls')),
]