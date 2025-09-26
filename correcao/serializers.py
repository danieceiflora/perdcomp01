from rest_framework import serializers
from .models import TeseCredito



class TeseCreditoSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = TeseCredito
        fields = ['id', 'id_correcao', 'descricao', 'jurisprudencia', 'corrige', 'cod_origem']
