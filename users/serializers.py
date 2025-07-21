import phonenumbers
from rest_framework import serializers
from users.models import Usuario

class EnviarOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    guid = serializers.UUIDField()
    login_session_code = serializers.CharField()

    def validate_login_session_code(self, value):
        if not value.isdigit() or len(value) != 6:
            raise serializers.ValidationError("El código de sesión debe tener 6 dígitos numéricos.")
        return value

    def validate_phone_number(self, value):
        try:
            parsed = phonenumbers.parse(value, 'CL')  # puedes cambiar 'CL' según tu país por defecto
            if not phonenumbers.is_valid_number(parsed):
                raise serializers.ValidationError("Número de teléfono inválido")

            return phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.E164
            )

        except phonenumbers.NumberParseException:
            raise serializers.ValidationError("Número de teléfono inválido")


class UsuarioLoginSerializer(serializers.ModelSerializer):
    phone_number = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = ['guid', 'phone_number', 'login_session_code']

    def get_phone_number(self, obj):
        if not obj.phone_number:
            return None
        return f"{obj.phone_number[:-3].replace(obj.phone_number[:-3], '*' * len(obj.phone_number[:-3]))}{obj.phone_number[-3:]}"


class VerifyOTPSerializer(serializers.Serializer):
    guid = serializers.UUIDField()
    otp_code = serializers.CharField(min_length=6, max_length=6)
    session_code = serializers.CharField(min_length=6, max_length=6)


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'guid', 'email', 'phone_number', 
                  'is_2fa_enabled', 'password', 'first_name', 'last_name']
        read_only_fields = ['id', 'guid']

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = Usuario(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user

    # Para aceptar password en el input
    password = serializers.CharField(write_only=True, required=True)


class UsuarioUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name', 'phone_number', 'email']


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("La nueva contraseña debe tener al menos 8 caracteres.")
        return value
