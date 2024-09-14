import datetime
import re
import logging
import csv
from .models import Branch
import pandas as pd
from .models import Staff, Role
from django.contrib.auth.models import User
from .tasks import send_staff_creation_email

logger = logging.getLogger(__name__)

def generate_unique_username(school_initials, last_name, current_year):
    """
    Generates a unique username in the format:
    SCHOOLINITIALS/LASTNAME/YEAR/COUNTER
    """
    base_username = f"{school_initials}-{last_name.upper()}-{current_year}"
    
    # Start with a counter of 1 and increment if necessary
    counter = 1
    unique_username = f"{base_username}-{counter}"

    # Keep incrementing the counter until a unique username is found
    while User.objects.filter(username=unique_username).exists():
        counter += 1
        unique_username = f"{base_username}-{counter}"
    
    return unique_username


def process_uploaded_file(file, file_name, branch, school):
    try:
        # Check if the file is a CSV
        if not file_name.endswith('.csv'):
            raise ValueError(f"Unsupported file type: {file_name}. Please upload a CSV file.")

        # Check for valid branch
        if not branch:
            raise ValueError("Branch could not be detected. Ensure the file name is correct.")

        # Try decoding with UTF-8 first, then fall back to UTF-16 if needed
        try:
            print("Attempting to decode file with UTF-8...")
            file_content = file.read().decode('utf-8')
        except UnicodeDecodeError:
            print("UTF-8 decoding failed, trying UTF-16...")
            file.seek(0)  # Reset file pointer to the beginning
            file_content = file.read().decode('utf-16')

        # Parse the file content using csv.DictReader
        data = csv.DictReader(file_content.splitlines())
        print(f"Processing file {file_name} for branch {branch.branch_name} in school {school.school_name}")

        headers = data.fieldnames
        print(f"CSV Headers: {headers}")
        
        # Validate required headers
        required_headers = {'first_name', 'last_name', 'email', 'role'}
        missing_headers = required_headers - set(headers)
        if missing_headers:
            raise ValueError(f"Missing required headers: {', '.join(missing_headers)}")
        
        # Determine if the file is for primary or secondary school based on file_name
        school_type = "Primary" if "Primary" in file_name else "Secondary"
        print(f"Detected school type: {school_type}")

        # Get school initials based on school type
        if school_type == "Primary" and hasattr(school, 'primary_school'):
            school_initials = ''.join([word[0].upper() for word in school.primary_school.school_name.split()])
        else:
            school_initials = ''.join([word[0].upper() for word in school.school_name.split()])

        print(f"Using school initials: {school_initials}")
        
        current_year = datetime.datetime.now().year

        for idx, row in enumerate(data):
            try:
                first_name = row.get('first_name', '').strip()
                last_name = row.get('last_name', '').strip()

                if not first_name or not last_name:
                    print(f"Skipping row {idx} due to missing first name or last name.")
                    continue

                # Generate a unique username
                username = generate_unique_username(school_initials, last_name, current_year)

                # Check if a user with the same username exists
                if User.objects.filter(username=username).exists():
                    print(f"User with username {username} already exists. Skipping row {idx}.")
                    continue

                email = row.get('email', '').strip()
                role_name = row.get('role', '').strip()

                if not email:
                    print(f"Skipping row {idx} due to missing email.")
                    continue
                
                # Get or create the role
                role, _ = Role.objects.get_or_create(name=role_name)
                print(f"Role found/created: {role_name}")

                # Create a new user
                user = User.objects.create_user(username=username, email=email, first_name=first_name, last_name=last_name.upper())
                user.set_password('new_staff')  # Set default password
                user.save()

                print(f"Created user: {user.username}")

                # Send email asynchronously using Celery
                send_staff_creation_email.delay(email, username, school.short_code)

                
                # Create or update the staff record
                staff, created = Staff.objects.update_or_create(user=user, defaults={
                    'role': role,
                    'gender': row.get('gender', '').strip(),
                    'marital_status': row.get('marital_status', '').strip(),
                    'date_of_birth': row.get('date_of_birth', None),
                    'phone_number': row.get('phone_number', '').strip(),
                    'address': row.get('address', '').strip(),
                    'nationality': row.get('nationality', '').strip(),
                    'staff_category': row.get('staff_category', '').strip(),
                    'status': row.get('status', '').strip(),
                })

                # Assign the staff to the branch
                staff.branches.add(branch)
                print(f"Assigned staff {user.username} to branch {branch.branch_name}")

            except Exception as e:
                print(f"Error processing row {idx}: {e}")
                continue

    except Exception as e:
        print(f"Error processing file {file_name}: {e}")
        raise

def normalize_branch_name_for_matching(branch_name):
    # Convert to lowercase
    branch_name = branch_name.lower()
    # Replace underscores with spaces
    branch_name = branch_name.replace("_", " ")
    # Remove any special characters (like parentheses)
    branch_name = re.sub(r'[^\w\s]', '', branch_name)
    return branch_name

def extract_branch_from_filename(filename, school):
    # Match the pattern: SCHOOLINITIALS_Primary_BranchName_UUID_staff_template.csv
    match = re.search(r'^[A-Z]{1,}_+(Primary|Secondary)_(.*?)_\w{3}_staff_template\.csv$', filename, re.IGNORECASE)
    if match:
        branch_name = normalize_branch_name_for_matching(match.group(2).strip().lower())
        branch = Branch.objects.filter(branch_name__iexact=branch_name, school=school).first()
        return branch
    return None

def is_valid_staff_file_name(file_name, school):
    """
    Validates the staff file name against the expected format.
    The format should be:
    PRIMARYSCHOOLINITIALS_Primary_BranchName_UUID_staff_template.csv
    or
    SECONDARYSCHOOLINITIALS_Secondary_BranchName_UUID_staff_template.csv
    """
    # Extract initials for the primary and secondary schools
    primary_school_initials = ''.join([word[0].upper() for word in school.primary_school.school_name.split()]) if hasattr(school, 'primary_school') else None
    secondary_school_initials = ''.join([word[0].upper() for word in school.school_name.split()])

    # Print to check what initials are being used for validation
    print(f"Validating against primary school initials: {primary_school_initials}")
    print(f"Validating against secondary school initials: {secondary_school_initials}")

    # Regex pattern for both primary and secondary schools
    file_name_pattern = rf'^({primary_school_initials}|{secondary_school_initials})_(Primary|Secondary)_(.*?)_\w{{3}}_staff_template\.csv$'
    
    # Print the file name being validated
    print(f"Validating file name: {file_name}")

    # Match the filename against the pattern
    match = re.match(file_name_pattern, file_name, re.IGNORECASE)
    
    # Print whether the match was successful
    if match:
        print("File name is valid.")
    else:
        print("File name is invalid.")
    
    # Return True if the filename matches the expected pattern, otherwise False
    return bool(match)