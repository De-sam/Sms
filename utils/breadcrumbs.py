from django.shortcuts import get_object_or_404
from landingpage.models import SchoolRegistration

def dynamic_breadcrumbs(request):
    """
    Generate dynamic breadcrumbs with a consistent root for school-related paths.
    """
    breadcrumbs = []
    path = request.path.strip('/').split('/')

    # Ensure at least <dynamic>/<school_code>/<dynamic> structure
    if len(path) > 1:
        school_code = path[1]  # Extract school code dynamically
        # Validate school existence for consistent root
        school = get_object_or_404(SchoolRegistration, short_code=school_code)

        # Add consistent root for school paths
        breadcrumbs.append({'name': 'Dashboard', 'url': f'/schools/{school_code}/dashboard/'})

        # Dynamically build breadcrumbs for additional segments
        for i in range(2, len(path)):
            name = path[i].replace('-', ' ').capitalize()
            url = '/' + '/'.join(path[:i + 1]) + '/'
            breadcrumbs.append({'name': name, 'url': url})
    else:
        # Fallback for non-school paths
        breadcrumbs.append({'name': 'Home', 'url': '/'})

    return {'breadcrumbs': breadcrumbs}
