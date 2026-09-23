from rest_framework import serializers
from .models import Lote, Dispositivo

class LoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lote
        fields = '__all__'

class DispositivoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dispositivo
        fields = '__all__'
