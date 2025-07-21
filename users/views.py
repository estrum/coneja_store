# users/views.py
import random
import datetime
from time import sleep

from twilio.rest import Client

from django.conf import settings
from django.utils import timezone
from django.contrib.auth import authenticate

from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.throttling import UserRateThrottle

from users.serializers import (UsuarioLoginSerializer, 
                               EnviarOTPSerializer,
                               UsuarioSerializer,
                               UsuarioUpdateSerializer,
                               ChangePasswordSerializer)
from users.models import Usuario
from .permissions import IsAdminOrSuperUser


class LoginThrottle(UserRateThrottle):
    rate = '10/hour'

class LoginView(APIView):
    throttle_classes = [LoginThrottle]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response(
                {"detail": "Email y contraseña son requeridos"}, 
                status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, email=email, password=password)

        if user is None:
            sleep(random.randint(4, 10))
            return Response(
                {"detail": "Credenciales inválidas"}, 
                status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            sleep(random.randint(4, 10))
            return Response(
                {"detail": "Cuenta desactivada"}, 
                status=status.HTTP_403_FORBIDDEN)

        # Generar token temporal de 6 dígitos
        session_code = str(random.randint(100000, 999999))
        user.login_session_code = session_code
        user.login_session_expires_at = timezone.now() + datetime.timedelta(minutes=3)
        user.save()

        #Aquí podrías generar y enviar el código 2FA (por SMS o usar TOTP)
        serializer = UsuarioLoginSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class EnviarOTPView(APIView):
    throttle_classes = [UserRateThrottle]

    def post(self, request):
        serializer = EnviarOTPSerializer(data=request.data)
        session_code = request.data.get('login_session_code')
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        phone = serializer.validated_data['phone_number']

        try:
            user = Usuario.objects.get(phone_number=phone)
        except Usuario.DoesNotExist:
            sleep(random.randint(4, 10))
            return Response(
                {'detail': 'Credenciales inválidas'}, status=404)
        
        if session_code != user.login_session_code:
            sleep(random.randint(4, 10))
            return Response(
                {'detail': 'Credenciales inválidas'}, status=400)

        # Generar OTP de 6 dígitos
        otp_code = str(random.randint(100000, 999999))
        user.current_otp = otp_code
        user.code_expires_at = timezone.now() + datetime.timedelta(minutes=2)
        user.save()

        # Enviar SMS con Twilio
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=f"Tu código de verificación es: {otp_code}",
            from_=settings.TWILIO_PHONE_NUMBER,
            to=phone
        )

        return Response({'detail': 'Código enviado correctamente'}, status=200)


class VerificarOTPView(APIView):
    throttle_classes = [UserRateThrottle]

    def post(self, request):
        guid = request.data.get('guid')
        otp_code = request.data.get('otp_code')
        session_code = request.data.get('session_code')

        if not guid or not otp_code or not session_code:
            sleep(random.randint(4, 10))
            return Response(
                {"detail": "Credenciales inválidas"}, status=400)

        try:
            user = Usuario.objects.get(guid=guid)
        except Usuario.DoesNotExist:
            sleep(random.randint(4, 10))
            return Response({'detail': 'Credenciales inválidas'}, status=404)

        if not user.has_valid_otp(otp_code):
            sleep(random.randint(4, 10))
            return Response({'detail': 'Credenciales inválidas'}, status=401)
        
        if not user.has_valid_session_token(session_code):
            sleep(random.randint(4, 10))
            return Response({'detail': 'Credenciales inválidas'}, status=401)

        # Limpiar OTP después de validarlo
        user.last_2fa_verified_at = timezone.now()
        user.current_otp = None
        user.code_expires_at = None

        #limpiar token temporal despues de validar
        user.login_session_code = None
        user.login_session_expires_at = None
        user.save()

        refresh = RefreshToken.for_user(user)

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        })


class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def list(self, request):
        users = Usuario.objects.exclude(is_superuser=True)
        serializer = UsuarioSerializer(users, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        try:
            user = Usuario.objects.exclude(is_superuser=True).get(pk=pk)
        except Usuario.DoesNotExist:
            return Response({'detail': 'Usuario no encontrado'}, status=404)
        serializer = UsuarioSerializer(user)
        return Response(serializer.data)

    def partial_update(self, request, pk=None):
        try:
            user = Usuario.objects.exclude(is_superuser=True).get(pk=pk)
        except Usuario.DoesNotExist:
            return Response({'detail': 'Usuario no encontrado'}, status=404)
        serializer = UsuarioUpdateSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'detail': 'Usuario actualizado'})
        return Response(serializer.errors, status=400)

    @action(detail=True, methods=['post'], url_path='change-password')
    def change_password(self, request, pk=None):
        try:
            user = Usuario.objects.exclude(is_superuser=True).get(pk=pk)
        except Usuario.DoesNotExist:
            return Response({'detail': 'Usuario no encontrado'}, status=404)

        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({'detail': 'Contraseña actualizada'})
        return Response(serializer.errors, status=400)

    def destroy(self, request, pk=None):
        try:
            user = Usuario.objects.exclude(is_superuser=True).get(pk=pk)
        except Usuario.DoesNotExist:
            return Response({'detail': 'Usuario no encontrado'}, status=404)
        user.delete()
        return Response({'detail': 'Usuario eliminado'}, status=204)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, id):
        try:
            user_to_edit = Usuario.objects.get(id=id)
        except Usuario.DoesNotExist:
            return Response({'detail': 'Usuario no encontrado'}, status=404)

        is_admin = request.user.is_staff or request.user.is_superuser
        is_self = request.user == user_to_edit

        if not is_self and not is_admin:
            return Response({'detail': 'No tienes permiso para cambiar esta contraseña'}, status=403)

        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        old_password = serializer.validated_data.get('old_password')
        new_password = serializer.validated_data['new_password']

        if is_self:
            if not old_password:
                return Response({'detail': 'Debes ingresar tu contraseña actual'}, status=400)
            if not user_to_edit.check_password(old_password):
                return Response({'detail': 'Contraseña actual incorrecta'}, status=400)

        # Si es admin o superuser, no se valida old_password
        user_to_edit.set_password(new_password)
        user_to_edit.save()

        return Response({'detail': 'Contraseña actualizada correctamente'}, status=200)
