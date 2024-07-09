

def get_all_nigerian_states():
    return [
        'Select state','Abia', 'Adamawa', 'Akwa Ibom', 'Anambra', 'Bauchi', 'Bayelsa', 'Benue', 'Borno',
        'Cross River', 'Delta', 'Ebonyi', 'Edo', 'Ekiti', 'Enugu', 'Gombe', 'Imo', 'Jigawa',
        'Kaduna', 'Kano', 'Katsina', 'Kebbi', 'Kogi', 'Kwara', 'Lagos', 'Nasarawa', 'Niger',
        'Ogun', 'Ondo', 'Osun', 'Oyo', 'Plateau', 'Rivers', 'Sokoto', 'Taraba', 'Yobe', 'Zamfara'
    ]

def get_local_governments():
    return {
        'Abia': ['Aba North', 'Aba South', 'Arochukwu', ...],
        'Adamawa': ['Demsa', 'Fufore', ...],
        # Add other states and their local governments
    }

def generate_shortcode(school_name):
    print(school_name)
    return school_name[:5].upper()  #
    