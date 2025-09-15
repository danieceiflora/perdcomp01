from django import template
import re

register = template.Library()

@register.filter(name='format_cnpj')
def format_cnpj(cnpj):
    """
    Formata um CNPJ (com ou sem máscara) para o formato 00.000.000/0000-00.
    Funciona para CNPJs numéricos. Para alfanuméricos, retorna o valor como está.
    """
    if not cnpj:
        return ""
    
    # Remove todos os caracteres não numéricos para verificar se é um CNPJ tradicional
    cnpj_clean = re.sub(r'\D', '', str(cnpj))
    
    if len(cnpj_clean) == 14 and cnpj_clean.isdigit():
        return f"{cnpj_clean[0:2]}.{cnpj_clean[2:5]}.{cnpj_clean[5:8]}/{cnpj_clean[8:12]}-{cnpj_clean[12:14]}"
    
    # Se não for um CNPJ numérico padrão (pode ser o novo alfanumérico), retorna o valor original
    return cnpj

@register.filter(name='format_phone')
def format_phone(phone):
    """
    Formata um número de telefone para (00) 0000-0000 ou (00) 00000-0000.
    """
    if not phone:
        return ""
        
    phone_clean = re.sub(r'\D', '', str(phone))
    
    if len(phone_clean) == 11:
        return f"({phone_clean[0:2]}) {phone_clean[2:7]}-{phone_clean[7:11]}"
    elif len(phone_clean) == 10:
        return f"({phone_clean[0:2]}) {phone_clean[2:6]}-{phone_clean[6:10]}"
    
    return phone

@register.filter(name='brl')
def brl(valor):
    """Formata número em Real brasileiro (sem símbolo): 1.234,56."""
    if valor in (None, ""):
        return "0,00"
    from decimal import Decimal, InvalidOperation
    try:
        if isinstance(valor, str):
            # Normaliza vírgula decimal caso já venha formatado parcialmente
            valor_norm = valor.replace(' ', '').replace('.', '').replace(',', '.')
            valor = Decimal(valor_norm)
        else:
            valor = Decimal(str(valor))
        quant = valor.quantize(Decimal('0.01'))
        # Usa formatação padrão en-US com vírgula para milhar, ponto decimal e substitui
        base = f"{quant:,.2f}"  # ex: 1,234,567.89
        parte_int, parte_dec = base.split('.')
        parte_int = parte_int.replace(',', '.')  # vira 1.234.567
        return f"{parte_int},{parte_dec}"
    except (InvalidOperation, ValueError):
        return "0,00"
