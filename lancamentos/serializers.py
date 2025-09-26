from rest_framework import serializers
from .models import Lancamentos, Anexos


class AnexoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Anexos
        fields = '__all__'


class LancamentoSerializer(serializers.ModelSerializer):
    anexos = AnexoSerializer(many=True, read_only=True)

    class Meta:
        model = Lancamentos
        fields = '__all__'
