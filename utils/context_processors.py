# utils/context_processors.py
def global_context(request):
    context = {}
    if request.user.is_authenticated:
        context['force_password_change'] = request.session.pop('force_password_change', False)
    return context


def school_context(request):
    """
    Adds the current school's short_code to the context if it's available in the request.
    """
    if 'short_code' in request.resolver_match.kwargs:
        short_code = request.resolver_match.kwargs.get('short_code')
        return {'schoolshort_code': short_code}
    return {}
