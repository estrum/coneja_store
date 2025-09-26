from logs.models import Log
from rest_framework import serializers


class LogSerializer(serializers.ModelSerializer):
    """crud para categorías"""
    
    class Meta:
        model = Log
        fields = '__all__'
