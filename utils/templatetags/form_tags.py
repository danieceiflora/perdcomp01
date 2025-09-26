from django import template
from django.forms import Widget

register = template.Library()

@register.filter
def add_class(field, css_class):
    """
    Add CSS class to form field widget
    Usage: {{ form.field|add_class:"my-class" }}
    """
    if hasattr(field, 'field'):
        # This is a bound field
        widget = field.field.widget
    elif hasattr(field, 'widget'):
        # This is a form field
        widget = field.widget
    else:
        # This is likely a widget itself
        widget = field
    
    if hasattr(widget, 'attrs'):
        existing_classes = widget.attrs.get('class', '')
        if existing_classes:
            widget.attrs['class'] = f"{existing_classes} {css_class}"
        else:
            widget.attrs['class'] = css_class
    
    return field
