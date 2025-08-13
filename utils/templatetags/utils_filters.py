from django import template

register = template.Library()

@register.filter
def br_currency(value):
	"""Formata número em padrão brasileiro com 2 casas decimais.
	Accepts int, float, Decimal or str convertible. Returns string like 1.234,56.
	"""
	if value in (None, ''):
		return '--'
	try:
		# Converte para Decimal para precisão
		from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
		if isinstance(value, str):
			# Remove possíveis separadores já existentes
			cleaned = value.replace('.', '').replace(',', '.')
			value = Decimal(cleaned)
		else:
			value = Decimal(str(value))
		q = value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
		# Formata com separador milhar '.' e decimal ','
		inteiro, frac = f"{q:.2f}".split('.')
		partes = []
		while len(inteiro) > 3:
			partes.insert(0, inteiro[-3:])
			inteiro = inteiro[:-3]
		partes.insert(0, inteiro)
		return f"{'.'.join(partes)},{frac}"
	except (InvalidOperation, ValueError):
		return str(value)
