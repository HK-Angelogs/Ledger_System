from django.urls import path
from . import views

urlpatterns = [
    # Login Page
    path('', views.login_view, name='login'),

    # Logout
    path('logout/', views.logout_view, name='logout'),
]
