from django.db import models
from schools.models import Branch 


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Arm(models.Model):
    name = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.name

class Class(models.Model):
    name = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    arms = models.ManyToManyField(Arm, blank=True)
    branches = models.ManyToManyField(Branch, related_name='classes', blank=True)

    def __str__(self):
        return f"{self.name}  {self.department.name if self.department else ''}"
