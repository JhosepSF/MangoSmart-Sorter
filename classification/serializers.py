from rest_framework import serializers
from .models import Clasificacion

class ClasificacionSerializer(serializers.ModelSerializer):
    fecha_hora_formateada = serializers.SerializerMethodField()

    class Meta:
        model = Clasificacion
        fields = '__all__'

    def get_fecha_hora_formateada(self, obj):
        return obj.fecha_hora.strftime("%d/%m/%Y %H:%M:%S")
