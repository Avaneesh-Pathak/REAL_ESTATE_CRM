from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include


# from django.contrib.auth import views as auth_views
from django.contrib.auth.views import (
    LoginView, 
    LogoutView, 
    PasswordResetView, 
    PasswordResetDoneView, 
    PasswordResetConfirmView, 
    PasswordResetCompleteView,
)
from leads.views import LandingPageView, SignupView, DashboardView,update_profile,user_profile,search_view,custom_login_view

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('', LandingPageView.as_view(), name='landing_page'),
    path('profile/', user_profile, name='profile'),  # Profile view
    path('search/', search_view, name='search'),
    path('profile/update/', update_profile, name='update_profile'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('leads/', include('leads.urls', namespace='leads')),
    path('agents/', include('agents.urls', namespace='agents')),
    path('signup/', SignupView.as_view(), name='signup'),

    # Password reset URLs
    path('reset-password/', PasswordResetView.as_view(), name='reset_password'),
    path('reset-password-done/', PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset-password-complete/', PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # path('login/', LoginView.as_view(), name='login'),
    path('login/', custom_login_view, name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
  
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

