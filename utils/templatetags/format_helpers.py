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
