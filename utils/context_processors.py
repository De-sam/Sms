# utils/context_processors.py
def global_context(request):
    context = {}
    if request.user.is_authenticated:
        context['force_password_change'] = request.session.pop('force_password_change', False)
    return context
