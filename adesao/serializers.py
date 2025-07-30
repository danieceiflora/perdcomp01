from rest_framework import serializers
from adesao.models import Adesao

class AdesaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Adesao
        fields = '__all__'