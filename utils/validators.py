from django.core.exceptions import ValidationError
import re

def validate_cnpj(value):
    """
    Valida um CNPJ, suportando o formato puramente numérico (14 dígitos)
    e o novo formato alfanumérico anunciado para 2026.
    A validação do dígito verificador é adaptada para ambos os casos.
    """
    # Remove máscara (pontos, barras, traços)
    cnpj = ''.join(re.findall(r'[0-9A-Za-z]', value)).upper()

    if len(cnpj) != 14:
        raise ValidationError('O CNPJ deve conter 14 caracteres.')

    # Se for puramente numérico, usa a validação tradicional
    if cnpj.isdigit():
        if len(set(cnpj)) == 1:
            raise ValidationError('CNPJ inválido (todos os dígitos iguais).')
        
        try:
            # Cálculo do primeiro dígito verificador
            soma = 0
            peso = 5
            for i in range(12):
                soma += int(cnpj[i]) * peso
                peso -= 1
                if peso < 2:
                    peso = 9
            resto = soma % 11
            dv1 = 0 if resto < 2 else 11 - resto
            if dv1 != int(cnpj[12]):
                raise ValidationError('Dígito verificador do CNPJ inválido.')

            # Cálculo do segundo dígito verificador
            soma = 0
            peso = 6
            for i in range(13):
                soma += int(cnpj[i]) * peso
                peso -= 1
                if peso < 2:
                    peso = 9
            resto = soma % 11
            dv2 = 0 if resto < 2 else 11 - resto
            if dv2 != int(cnpj[13]):
                raise ValidationError('Dígito verificador do CNPJ inválido.')
        except (ValueError, IndexError):
            raise ValidationError('CNPJ com formato numérico inválido.')

    # Se for alfanumérico, usa a nova regra de cálculo
    else:
        if not re.match(r'^[A-Z0-9]{14}$', cnpj):
            raise ValidationError('CNPJ alfanumérico contém caracteres inválidos.')

        try:
            # Converte caracteres para valores numéricos baseados na tabela ASCII
            def get_char_value(char):
                return ord(char) - 48

            # Cálculo do primeiro dígito verificador
            soma = 0
            peso = 5
            for i in range(12):
                soma += get_char_value(cnpj[i]) * peso
                peso -= 1
                if peso < 2:
                    peso = 9
            resto = soma % 11
            dv1 = 0 if resto < 2 else 11 - resto
            if dv1 != int(cnpj[12]):
                raise ValidationError('Dígito verificador do CNPJ alfanumérico inválido.')

            # Cálculo do segundo dígito verificador
            soma = 0
            peso = 6
            for i in range(13):
                soma += get_char_value(cnpj[i]) * peso
                peso -= 1
                if peso < 2:
                    peso = 9
            resto = soma % 11
            dv2 = 0 if resto < 2 else 11 - resto
            if dv2 != int(cnpj[13]):
                raise ValidationError('Dígito verificador do CNPJ alfanumérico inválido.')
        except (ValueError, IndexError):
            raise ValidationError('CNPJ com formato alfanumérico inválido.')

    return value
