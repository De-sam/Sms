from django.db import models
from django.contrib.auth.models import User
import uuid

class SchoolRegistration(models.Model):
    REFERRAL_SOURCES = [
        ('facebook', 'Facebook'),
        ('linkedin', 'LinkedIn'),
        ('google', 'Google'),
        ('youtube', 'YouTube'),
        ('x', 'X'),
    ]

    school_name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    lga = models.CharField(max_length=100)
    short_code = models.CharField(max_length=50, unique=True)
    logo = models.ImageField(default='https://res.cloudinary.com/<cloud_name>/image/upload/v123456789/default.jpg', upload_to='logos')
    theme_color1 = models.CharField(max_length=7)
    theme_color2 = models.CharField(max_length=7)
    username = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    admin_phone_number = models.CharField(max_length=15)
    admin_user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='school')
    referral_source = models.CharField(max_length=50, choices=REFERRAL_SOURCES, default='other')
    school_id = models.CharField(max_length=10, unique=True, editable=False)
    admin_signature = models.ImageField(upload_to='signatures/', null=True, blank=True)


    class Meta:
        indexes = [
            models.Index(fields=['short_code']),
            models.Index(fields=['school_name']),
            models.Index(fields=['state']),
            models.Index(fields=['lga']),
            models.Index(fields=['email']),
            models.Index(fields=['admin_user']),
        ]

    @classmethod
    def generate_shortcode(cls, name):
        words = name.split()
        base_shortcode = ''.join([word[0] + word[-1] for word in words]).lower()

        short_code = base_shortcode
        counter = 1

        while cls.objects.filter(short_code=short_code).exists():
            short_code = f"{base_shortcode}{counter}"
            counter += 1

        return short_code

    def save(self, *args, **kwargs):
        if not self.school_id:
            self.school_id = f"{self.school_name[:3].upper()}{str(uuid.uuid4())[:4]}"
        if not self.short_code:
            self.short_code = self.generate_shortcode(self.school_name)
        super(SchoolRegistration, self).save(*args, **kwargs)

    def __str__(self):
        return (f"ID: {self.school_id}, "
                f"School: {self.school_name}, State: {self.state}, LGA: {self.lga}, "
                f"Admin: {self.first_name} {self.last_name}, "
                f"Phone: {self.admin_phone_number}, "
                f"Short Code: {self.short_code}")

    def is_secondary_school(self):
        return True  # Every SchoolRegistration is considered a Secondary School
