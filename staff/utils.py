
import re
import logging
import csv
from .models import Branch
import pandas as pd
from .models import Staff, Role
from django.contrib.auth.models import User
from .tasks import send_staff_creation_email

logger = logging.getLogger(__name__)

def generate_unique_username(last_name, school_name):
    # Extract the first 3 letters of the school's name in uppercase
    school_prefix = school_name[:3].upper()
    # Ensure the last name is fully capitalized
    last_name = last_name.upper()
    base_username = f"{school_prefix}/{last_name}/"
    counter = 1

    # Find the next available unique username
    while True:
        username = f"{base_username}{counter}"  # Natural counter (1, 2, 3, etc.)
        if not User.objects.filter(username=username).exists():
            break
        counter += 1

    return username



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
        
        for idx, row in enumerate(data):
            try:
                first_name = row.get('first_name', '').strip()
                last_name = row.get('last_name', '').strip()

                if not first_name or not last_name:
                    print(f"Skipping row {idx} due to missing first name or last name.")
                    continue

                # Generate a unique username
                username = generate_unique_username(last_name, school.school_name)

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
    match = re.search(r'^(Primary|College)_(.*?)_staff_template\.csv$', filename, re.IGNORECASE)  # Updated to .csv
    if match:
        branch_name = normalize_branch_name_for_matching(match.group(2).strip().lower())
        branch = Branch.objects.filter(branch_name__iexact=branch_name, school=school).first()
        return branch
    return None

