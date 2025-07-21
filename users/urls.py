# users/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from users.views import (LoginView, 
                         EnviarOTPView, 
                         VerificarOTPView,
                         UsuarioViewSet,
                         ChangePasswordView)

router = DefaultRouter()
router.register(r'user-admin', UsuarioViewSet, basename='user-admin')

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('send-otp/', EnviarOTPView.as_view(), name='send-otp'),
    path('verify-otp/', VerificarOTPView.as_view()),
    path('user-admin/<int:id>/change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('', include(router.urls)),
]


