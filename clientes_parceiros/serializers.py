from rest_framework import serializers
from .models import ClientesParceiros

class ClientesParceirosSerializer(serializers.ModelSerializer):
    id_company_base_id = serializers.PrimaryKeyRelatedField(source='id_company_base', queryset=ClientesParceiros._meta.get_field('id_company_base').remote_field.model.objects.all(), write_only=True)
    id_company_vinculada_id = serializers.PrimaryKeyRelatedField(source='id_company_vinculada', queryset=ClientesParceiros._meta.get_field('id_company_vinculada').remote_field.model.objects.all(), write_only=True)

    id_company_base = serializers.StringRelatedField(read_only=True)
    id_company_vinculada = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = ClientesParceiros
        fields = [
            'id', 'tipo_parceria', 'id_company_base', 'id_company_vinculada',
            'id_company_base_id', 'id_company_vinculada_id', 'nome_referencia',
            'cargo_referencia', 'data_inicio_parceria', 'ativo'
        ]
        read_only_fields = ['data_inicio_parceria']

    def create(self, validated_data):
        return ClientesParceiros.objects.create(**validated_data)
