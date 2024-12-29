from django.shortcuts import get_object_or_404
from landingpage.models import SchoolRegistration

def dynamic_breadcrumbs(request):
    """
    Generate dynamic breadcrumbs with a consistent root for school-related paths.
    """
    breadcrumbs = []
    path = request.path.strip('/').split('/')

    if len(path) > 1 and path[0] == 'schools':
        # Extract the school code and validate
        school_code = path[1]
        try:
            school = SchoolRegistration.objects.get(short_code=school_code)
        except SchoolRegistration.DoesNotExist:
            # Invalid school code; return Home breadcrumb
            return {'breadcrumbs': [{'name': 'Home', 'url': '/'}]}

        # Add the consistent Dashboard root
        breadcrumbs.append({'name': 'Dashboard', 'url': f'/schools/{school_code}/dashboard/'})

        # Dynamically build the rest of the breadcrumbs
        for i in range(2, len(path)):
            # Ignore `dashboard` as it's already added as the root
            if path[i].lower() == 'dashboard' and i == 2:
                continue
            name = path[i].replace('-', ' ').capitalize()
            url = '/' + '/'.join(path[:i + 1]) + '/'
            breadcrumbs.append({'name': name, 'url': url})
    else:
        # Handle non-school paths (e.g., Django Admin)
        breadcrumbs.append({'name': 'Home', 'url': '/'})

    return {'breadcrumbs': breadcrumbs}
