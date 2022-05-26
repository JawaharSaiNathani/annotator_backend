# from django.db import models
from django.contrib.auth.models import AbstractUser
from djongo import models


class User(AbstractUser):
    _id = models.ObjectIdField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(default='', blank=True)

    # path for user profile picture
    def get_upload_path(instance, filename):
        return 'static/users/{0}/images/{1}'.format(instance.username, filename)

    image = models.ImageField(upload_to=get_upload_path, blank=True)
    username = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=255)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []


class Project(models.Model):
    _id = models.ObjectIdField(primary_key=True)
    title = models.CharField(max_length=255)
    description = models.TextField(default='', blank=True)

    creator = models.ForeignKey(User, on_delete=models.CASCADE)     # Project created by
    owners = models.ManyToManyField(User, blank=True, symmetrical=False, related_name='owner')      # List of Project owners
    staff = models.ManyToManyField(User, blank = True, symmetrical=False, related_name='staff')     # List of Project staff


# User notifications
class Notification(models.Model):
    _id = models.ObjectIdField(primary_key=True)
    title = models.CharField(max_length=255)
    description = models.TextField(default='', blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_notifications')


# Request choices
requestStatusChoices = (
    ("1", "is_pending"),
    ("2", "accepted"),
    ("3", "declined"),
)
requestRoleChoices = (
    ("1", "owner"),
    ("2", "staff"),
)
requestTerminalChoices = (
    ("1", "user"),
    ("2", "project"),
)

class Request(models.Model):
    _id = models.ObjectIdField(primary_key=True)
    title = models.CharField(max_length=255)
    description = models.TextField(default='', blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)        # Request's user
    project = models.ForeignKey(Project, on_delete=models.CASCADE)      # Request's project
    role = models.CharField(max_length=20, choices = requestRoleChoices, default='2')       # User role in Project
    terminal = models.CharField(max_length=20, choices = requestTerminalChoices, default='1')       # Request initiated by [ User | Project ]
    status = models.CharField(max_length=20, choices = requestStatusChoices, default='1')       # Request status


class Document(models.Model):
    _id = models.ObjectIdField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(default='', blank=True)

    # path for document image
    def get_upload_path(instance, filename):
        return 'static/projects/{0}/documents/{1}'.format(instance.project.title.replace(' ', '') + '_' + str(instance.project._id), filename)

    image = models.ImageField(upload_to=get_upload_path,blank=True)
    is_annotated = models.BooleanField(default=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="documents")        # Document => Project


class Annotation(models.Model):
    _id = models.ObjectIdField(primary_key=True)
    name = models.CharField(max_length=255)
    topX = models.FloatField(default=0)
    topY = models.FloatField(default=0)
    bottomX = models.FloatField(default=0)
    bottomY = models.FloatField(default=0)
    is_antipattern = models.BooleanField(default=False)
    ground_truth = models.BooleanField(default=True)        # True -> [if verified by user] | False -> [not verified by user(predicted annotations)]
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="annotations")
    user = models.ForeignKey(User, on_delete=models.CASCADE)


class AnnotationModel(models.Model):
    _id = models.ObjectIdField(primary_key=True)
    name = models.CharField(max_length=255)
    avgWidth = models.FloatField(default=0)
    avgHeight = models.FloatField(default=0)

    # path for model file
    def get_upload_path(instance, filename):
        return 'static/models/' + instance.name.replace(' ', '') + '_' + str(instance.user._id) + '.pth'

    model = models.FileField(upload_to=get_upload_path)
    model_pool = models.CharField(max_length=24)        # Annotation model main Modelpool
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)


class ModelPool(models.Model):
    _id = models.ObjectIdField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(default='', blank=True)

    modelpool_list = models.ManyToManyField('self', blank = True, symmetrical=False, related_name='sub_modelpools')     # List of sub-modelpools
    pool_models = models.ManyToManyField(AnnotationModel, blank=True, related_name='pool_models', symmetrical=False)    # List of models
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="project_modelpools")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_modelpools")


# To track status of sub-modelpools in main-modelpool
class ModelPoolStatus(models.Model):
    _id = models.ObjectIdField(primary_key=True)
    main_modelpool = models.ForeignKey(ModelPool, on_delete=models.CASCADE, related_name="main_modelpool")
    sub_modelpool = models.ForeignKey(ModelPool, on_delete=models.CASCADE, related_name="sub_modelpool")
    is_active = models.BooleanField(default=True)