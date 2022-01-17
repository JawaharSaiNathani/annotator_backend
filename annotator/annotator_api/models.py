from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    name = models.CharField(max_length=255)
    description = models.TextField(default='', blank=True)
    username = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=255)

    annotator_list = models.ManyToManyField('self', blank = True, symmetrical=False, related_name='annotators')

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

class Document(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(default='', blank=True)
    image = models.ImageField(upload_to='static/images/')
    user = models.ForeignKey(User, on_delete=models.CASCADE)

class Annotation(models.Model):
    name = models.CharField(max_length=255)
    topX = models.FloatField(default=0)
    topY = models.FloatField(default=0)
    bottomX = models.FloatField(default=0)
    bottomY = models.FloatField(default=0)
    document = models.ForeignKey(Document, on_delete=models.CASCADE)

class AnnotationModel(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(default='', blank=True)
    avgWidth = models.FloatField(default=0)
    avgHeight = models.FloatField(default=0)
    model_path = models.CharField(max_length=255, default='')
    is_active = models.BooleanField(default=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

class ModelPool(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(default='', blank=True)
    is_active = models.BooleanField(default=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="modelpool_user_set")
    modelpool_list = models.ManyToManyField('self', blank = True, symmetrical=False, related_name='sub_modelpools')
    subdescription_list = models.TextField(default='', blank=True)
    models = models.ManyToManyField(AnnotationModel, related_name='models', symmetrical=False)

requestStatusChoices = (
    ("1", "is_pending"),
    ("2", "accepted"),
    ("3", "declined"),
)

class Request(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(default='', blank=True)
    raised_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name = "request_raisedby")
    raised_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name = "request_for")
    status = models.CharField(max_length=20, choices = requestStatusChoices, default='1')