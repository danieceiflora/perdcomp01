from rest_framework import serializers
from .models import Correcao, tipoTese, TeseCredito

class CorrecaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Correcao
        fields = ['id', 'descricao', 'fonte_correcao', 'cod_origem']

class TipoTeseSerializer(serializers.ModelSerializer):
    class Meta:
        model = tipoTese
        fields = ['id', 'descricao', 'periodicidade']

class TeseCreditoSerializer(serializers.ModelSerializer):
    id_correcao = serializers.PrimaryKeyRelatedField(queryset=Correcao.objects.all(), required=False, allow_null=True)
    id_tipo_tese = serializers.PrimaryKeyRelatedField(queryset=tipoTese.objects.all())

    class Meta:
        model = TeseCredito
        fields = ['id', 'id_correcao', 'id_tipo_tese', 'descricao', 'jurisprudencia', 'corrige', 'cod_origem']
