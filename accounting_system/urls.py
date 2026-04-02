from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect


def redirect_to_login(request):
    return redirect('login')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('Users.urls')),
    path('ledger/', include('ledger.urls')),

    # Add this line to handle the empty path ''
    path('', redirect_to_login),
]
