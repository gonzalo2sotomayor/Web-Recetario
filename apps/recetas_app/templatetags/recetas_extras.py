from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    Permite acceder a un elemento de un diccionario por su clave.
    Uso: {{ my_dict|get_item:my_key }}
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    # Si 'categories' es un QuerySet de objetos Categoria, y 'key' es el slug,
    # podemos buscar el objeto por slug y devolver su nombre.
    elif hasattr(dictionary, 'filter'): # Asumimos que es un QuerySet
        try:
            # Intentamos encontrar la categoría por su slug
            return dictionary.filter(slug=key).first().nombre
        except AttributeError:
            # Si no se encuentra o no tiene 'nombre'
            return None
    return None # En caso de que no sea ni dict ni QuerySet manejable
