from django.db import models
from django.db.models.signals import post_save
import uuid
from django.dispatch import receiver 

class ListField(models.TextField):
    #Convert the database value to a list.
    def from_db_value(self, value, expression, connection):
        if value is None:
            return []
        return value.split(',')

    #Convert the input value to a list.
    def to_python(self, value):
        if isinstance(value, list):
            return value
        if value is None:
            return []
        return value.split(',')

    #Convert the list to a database value.
    def get_prep_value(self, value): 
        return ','.join(value)
    
class Control(models.Model):
    name = models.TextField(primary_key=True,unique=True)
    description = models.TextField()

class ControlSetReference(models.Model):
    reference_id = models.TextField(default=None, null=True)
    name = models.TextField(primary_key=True)
    
    def __str__(self):
            return f"{self.reference_id}"

class ControlSet(models.Model):
    slug = models.TextField( primary_key=True, editable=False, default=(uuid.uuid4))
    name = models.TextField(unique=True)
    hierarchy_depth = models.IntegerField()
    
def get_empty_queryset():
    return ControlHierarchy.objects.none()

class ControlHierarchy(models.Model):
    slug = models.TextField(primary_key=True, editable=False, default=(uuid.uuid4))
    control_set = models.ManyToManyField(ControlSetReference, blank=True, related_name='control_hierarchies', default=get_empty_queryset)
    parents = ListField(default=["None"])
    children = ListField(default=["None"])

@receiver(post_save, sender=ControlSet)
def create_control_hierarchy(instance, created, **kwargs):
    if created:
        ControlHierarchy.objects.create(slug=instance.slug)

@receiver(post_save, sender=Control)
def create_control_set_reference(instance, created, **kwargs):
    if created:
        ControlSetReference.objects.create(name=instance.name)