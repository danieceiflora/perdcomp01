from rest_framework import serializers
from .models import tipoTese, TeseCredito


class TipoTeseSerializer(serializers.ModelSerializer):
    class Meta:
        model = tipoTese
        fields = ['id', 'descricao', 'periodicidade']

class TeseCreditoSerializer(serializers.ModelSerializer):
    id_tipo_tese = serializers.PrimaryKeyRelatedField(queryset=tipoTese.objects.all())

    class Meta:
        model = TeseCredito
        fields = ['id', 'id_correcao', 'id_tipo_tese', 'descricao', 'jurisprudencia', 'corrige', 'cod_origem']
