# from django.db import models
from django.contrib.auth.models import AbstractUser
from djongo import models


class User(AbstractUser):
    _id = models.ObjectIdField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(default='', blank=True)

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

    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    owners = models.ManyToManyField(User, blank=True, symmetrical=False, related_name='owner')
    staff = models.ManyToManyField(User, blank = True, symmetrical=False, related_name='staff')



class Notification(models.Model):
    _id = models.ObjectIdField(primary_key=True)
    title = models.CharField(max_length=255)
    description = models.TextField(default='', blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_notifications')



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
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices = requestRoleChoices, default='2')
    terminal = models.CharField(max_length=20, choices = requestTerminalChoices, default='1')
    status = models.CharField(max_length=20, choices = requestStatusChoices, default='1')



class Document(models.Model):
    _id = models.ObjectIdField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(default='', blank=True)

    def get_upload_path(instance, filename):
        return 'static/projects/{0}/documents/{1}'.format(instance.project.title.replace(' ', '') + '_' + str(instance.project._id), filename)

    image = models.ImageField(upload_to=get_upload_path,blank=True)
    is_annotated = models.BooleanField(default=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="documents")



class Annotation(models.Model):
    _id = models.ObjectIdField(primary_key=True)
    name = models.CharField(max_length=255)
    topX = models.FloatField(default=0)
    topY = models.FloatField(default=0)
    bottomX = models.FloatField(default=0)
    bottomY = models.FloatField(default=0)
    is_antipattern = models.BooleanField(default=False)
    ground_truth = models.BooleanField(default=True)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="annotations")
    user = models.ForeignKey(User, on_delete=models.CASCADE)



class AnnotationModel(models.Model):
    _id = models.ObjectIdField(primary_key=True)
    name = models.CharField(max_length=255)
    avgWidth = models.FloatField(default=0)
    avgHeight = models.FloatField(default=0)

    def get_upload_path(instance, filename):
        return 'static/models/' + instance.name.replace(' ', '') + '_' + str(instance._id) + '.pth'

    model = models.FileField(upload_to=get_upload_path)
    model_pool = models.IntegerField()



class ModelPool(models.Model):
    _id = models.ObjectIdField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(default='', blank=True)

    modelpool_list = models.ManyToManyField('self', blank = True, symmetrical=False, related_name='sub_modelpools')
    subdescription_list = models.TextField(default='', blank=True)
    pool_models = models.ManyToManyField(AnnotationModel, related_name='models', symmetrical=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)



class ModelPoolStatus(models.Model):
    _id = models.ObjectIdField(primary_key=True)
    main_modelpool = models.ForeignKey(ModelPool, on_delete=models.CASCADE, related_name="main_modelpool")
    sub_modelpool = models.ForeignKey(ModelPool, on_delete=models.CASCADE, related_name="sub_modelpool")
    is_active = models.BooleanField(default=True)