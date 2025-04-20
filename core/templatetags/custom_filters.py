from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Get an item from a dictionary using the key.
    Usage: {{ my_dict|get_item:key_var }}
    """
    return dictionary.get(key)
