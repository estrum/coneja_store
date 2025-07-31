import phonenumbers
from rest_framework import serializers
from users.models import CustomUser

class SendOTPSerializer(serializers.Serializer):
    """Logica para enviar el sms con el codigo"""

    phone_number = serializers.CharField()
    guid = serializers.UUIDField()
    login_session_code = serializers.CharField()

    def validate_login_session_code(self, value):
        """valida que se ingrese un numero y que sea de 6 digitos"""
        if not value.isdigit() or len(value) != 6:
            raise serializers.ValidationError(
                "El código de sesión debe tener 6 dígitos numéricos.")

        return value

    def validate_phone_number(self, value):
        """valida que se ingrese un telefono chileno"""
        try:
            parsed = phonenumbers.parse(value, 'CL')
            print(parsed)
            if not phonenumbers.is_valid_number(parsed):
                raise serializers.ValidationError(
                    "Número de teléfono inválido")

            return phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.E164
            )

        except phonenumbers.NumberParseException:
            raise serializers.ValidationError(
                "Número de teléfono inválido")


class UserLoginSerializer(serializers.ModelSerializer):
    """Valida que el correo y la contraseña sean correctas"""
    phone_number = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['guid', 'phone_number', 'login_session_code']

    def get_phone_number(self, obj):
        if not obj.phone_number:
            return None
        return f"{obj.phone_number[:-3].replace(
            obj.phone_number[:-3],'*' * len(
                obj.phone_number[:-3]))}{obj.phone_number[-3:]}"


class VerifyOTPSerializer(serializers.Serializer):
    """Verifica el codigo del mensaje de texto"""
    guid = serializers.UUIDField()
    otp_code = serializers.CharField(min_length=6, max_length=6)
    login_session_code = serializers.CharField(min_length=6, max_length=6)


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    slug = serializers.SlugField(read_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'guid', 'slug', 'email', 'phone_number', 
                  'store_name', 'is_2fa_enabled', 'password', 
                  'first_name', 'last_name']
        read_only_fields = ['id', 'guid', 'slug']

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = CustomUser(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Actualiza el usuario sin modificar el password"""
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 
            'store_name', 'phone_number', 'email']


class ChangePasswordSerializer(serializers.Serializer):
    """Modifica la contraseña del usuario"""
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError(
                "La nueva contraseña debe tener al menos 8 caracteres.")
        return value