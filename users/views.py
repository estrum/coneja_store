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
from rest_framework.permissions import (IsAuthenticated,
                                        IsAdminUser)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.throttling import AnonRateThrottle

from users.serializers import (UserLoginSerializer, 
                               SendOTPSerializer,
                               UserSerializer,
                               UserUpdateSerializer,
                               ChangePasswordSerializer)
from users.models import CustomUser

from logs.utils import create_log

from conf.permissions import IsOwnerByGUIDOrAdminForUserApp


class PublicReadOnly(viewsets.ModelViewSet):
    # Permiso base, se anula en get_permissions
    permission_classes = [IsAuthenticated] 

    def get_permissions(self):
        if self.action in ['retrieve', 
                           'update', 
                           'partial_update', 
                           'destroy', 
                           'change_password']:
            # Para estas acciones, aplica IsOwnerByGUIDOrAdminForUserApp
            # Esto cubrirá retrieve, update, partial_update, 
            # destroy y la acción personalizada change_password.
            return [IsOwnerByGUIDOrAdminForUserApp()]
        elif self.action in ['list', 'create']:
            # Para list y create, solo administradores.
            return [IsAdminUser()]
        # Fallback para otras acciones no especificadas, 
        # aunque en un ModelViewSet esto es raro.
        return [permission() for permission in self.permission_classes]


class LoginThrottle(AnonRateThrottle):
    """limita las solicitudes a 20 por hora"""

    rate = '20/hour'


class LoginView(APIView):
    """Endpoint para login"""

    throttle_classes = [LoginThrottle]

    def post(self, request):
        """funcion para cuando se envía un formulario de sesión"""
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
        user.login_session_expires_at = (
            timezone.now() + datetime.timedelta(minutes=3))
        user.save()

        #Aquí podrías generar y enviar el código 2FA (por SMS o usar TOTP)
        serializer = UserLoginSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SendOTPView(APIView):
    """
    endpoint que verifica el codigo de sesión y manda sms
    con codigo para recibir el token 
    """
    throttle_classes = [LoginThrottle]

    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        session_code = request.data.get('login_session_code')

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        phone = serializer.validated_data['phone_number']

        try:
            user = CustomUser.objects.get(phone_number=phone)
            print(user)
        except CustomUser.DoesNotExist:
            sleep(random.randint(4, 10))
            return Response(
                {'detail': 'Credenciales inválidas'}, status=404)
        
        if session_code != user.login_session_code:
            sleep(random.randint(4, 10))
            return Response(
                {'detail': 'Credenciales inválidas'}, status=400)

        #TODO: descomentar las lineas de codigo de 3 comillas
        # Generar OTP de 6 dígitos
        """otp_code = str(random.randint(100000, 999999))
        user.current_otp = otp_code"""
        #TODO: eliminar codigo de la linea 133
        user.current_otp = 123456
        user.code_expires_at = (
            timezone.now() + datetime.timedelta(minutes=2))
        user.save()

        #TODO: descomentar las lineas de codigo de 3 comillas
        # Enviar SMS con Twilio
        """client = Client(
            settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=f"Tu código de verificación es: {otp_code}",
            from_=settings.TWILIO_PHONE_NUMBER,
            to=phone
        )"""

        return Response(
            {'detail': 'Código enviado correctamente'}, status=200)


class VerificarOTPView(APIView):
    """
    endpoint que valida el sms enviado al usuario y entrega el token para
    ingresar a su panel de administración
    """

    throttle_classes = [LoginThrottle]

    def post(self, request):
        guid = request.data.get('guid')
        otp_code = request.data.get('otp_code')
        login_session_code = request.data.get('login_session_code')

        if not guid or not otp_code or not login_session_code:
            sleep(random.randint(4, 10))
            return Response(
                {"detail": "Credenciales inválidas"}, status=400)

        try:
            user = CustomUser.objects.get(guid=guid)
        except CustomUser.DoesNotExist:
            sleep(random.randint(4, 10))
            return Response({'detail': 'Credenciales inválidas'}, 
                            status=404)

        if not user.has_valid_otp(otp_code):
            sleep(random.randint(4, 10))
            return Response({'detail': 'Credenciales inválidas'}, 
                            status=401)
        
        if not user.has_valid_session_token(login_session_code):
            sleep(random.randint(4, 10))
            return Response({'detail': 'Credenciales inválidas'}, 
                            status=401)

        # Limpiar OTP después de validarlo
        user.last_2fa_verified_at = timezone.now()
        user.current_otp = None
        user.code_expires_at = None

        #limpiar token temporal despues de validar
        user.login_session_code = None
        user.login_session_expires_at = None
        user.save()

        refresh = RefreshToken.for_user(user)

        #log
        create_log(
            user=user,
            action="LOGIN",
            message=f"User {user.first_name} logged",
            related_model="USER",
        )

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        })


class UserViewSet(PublicReadOnly):
    """Endpoints para usuarios"""

    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer

    def list(self, request):
        """GET"""
        users = CustomUser.objects.filter(
            is_superuser=False,
            is_active=True
        )
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    
    def retrieve(self, request, pk=None):
        """GET BY ID"""

        try:
            id= int(pk)
            user = CustomUser.objects.filter(
                is_superuser=False,
                is_active=True
            ).get(pk=id)
        
        except (ValueError, CustomUser.DoesNotExist):
            return Response(
                {'detail': 'Usuario no encontrado'}, status=404)
        
        self.check_object_permissions(request, user)
        serializer = UserSerializer(user)
        return Response(serializer.data)

    
    def partial_update(self, request, pk=None):
        """UPDATE (PATCH)"""
        
        try:
            id = int(pk)
            user = CustomUser.objects.exclude(
                is_superuser=True, is_active=False).get(pk=id)
        
        except (ValueError, CustomUser.DoesNotExist):
            return Response({'detail': 'CustomUser no encontrado'}, 
                            status=404)
        
        self.check_object_permissions(request, user)
        serializer = UserUpdateSerializer(user, 
                                          data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()

            #log
            create_log(
                user=user,
                action="UPDATE",
                message=f"User {user.first_name} updated!",
                related_model="USER",
            )

            return Response({'detail': 'CustomUser actualizado'})

        return Response(serializer.errors, status=400)

    
    @action(detail=True, methods=['post'], url_path='change-password')
    def change_password(self, request, pk=None):
        """UPDATE PASSWORD (PATCH)"""

        try:
            id = int(pk)
            user = CustomUser.objects.exclude(
                is_superuser=True, is_active=False).get(pk=id)
        
        except (ValueError, CustomUser.DoesNotExist):
            return Response(
                {'detail': 'CustomUser no encontrado'}, status=404)

        self.check_object_permissions(request, user)
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user.set_password(
                serializer.validated_data['new_password'])
            user.save()

            #log
            create_log(
                user=user,
                action="UPDATE",
                message=f"User {user.first_name}'s password changed!",
                related_model="USER",
            )

            return Response({'detail': 'Contraseña actualizada'})
        
        return Response(serializer.errors, status=400)

    
    def destroy(self, request, pk=None):
        """DELETE BY ID"""

        try:
            id = int(pk)
            user = CustomUser.objects.exclude(is_superuser=True).get(pk=id)
        except (ValueError, CustomUser.DoesNotExist):
            return Response({'detail': 'CustomUser no encontrado'}, status=404)
        
        self.check_object_permissions(request, user)
        user.is_active = False
        user.save()

        #log
        create_log(
            user=user,
            action="DELETE",
            message=f"User {user.first_name} deleted",
            related_model="USER",
        )

        return Response(
            {'detail': 'CustomUser eliminado'}, status=204)


class ChangePasswordView(APIView):
    """CAMBIA LA CONTRASEÑA"""

    permission_classes = [IsOwnerByGUIDOrAdminForUserApp]

    def patch(self, request, id):
        try:
            user_to_edit = CustomUser.objects.get(id=id)
        
        except CustomUser.DoesNotExist:
            return Response(
                {'detail': 'CustomUser no encontrado'}, status=404)

        self.check_object_permissions(request, user_to_edit)

        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        old_password = serializer.validated_data.get('old_password')
        new_password = serializer.validated_data['new_password']

        # La lógica de old_password solo aplica si el usuario no es 
        # admin/superuser y está cambiando su propia contraseña.
        if not (
            request.user.is_staff 
            or request.user.is_superuser
            ) and request.user == user_to_edit:
            
            if not old_password:
                return Response(
                    {'detail': 'Debes ingresar tu contraseña actual'}, 
                    status=400)
            if not user_to_edit.check_password(old_password):
                return Response(
                    {'detail': 'Contraseña actual incorrecta'}, 
                    status=400)

        # Si es admin o superuser, no se valida old_password
        user_to_edit.set_password(new_password)
        user_to_edit.save()

        return Response(
            {'detail': 'Contraseña actualizada correctamente'}, 
            status=200)
