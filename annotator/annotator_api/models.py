from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    name = models.CharField(max_length=255)
    description = models.TextField(default='', blank=True)

    def get_upload_path(instance, filename):
        return 'static/users/{0}/images/{1}'.format(instance.username, filename)

    image = models.ImageField(upload_to=get_upload_path, blank=True)
    username = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=255)

    annotator_list = models.ManyToManyField('self', blank = True, symmetrical=False, related_name='annotators')
    project_list = models.ManyToManyField('self', blank = True, symmetrical=False, related_name='projects')

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

class Notification(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(default='', blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

requestStatusChoices = (
    ("1", "is_pending"),
    ("2", "accepted"),
    ("3", "declined"),
)
requestTypeChoices = (
    ("1", "work"),
    ("2", "hire"),
)

class Request(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(default='', blank=True)
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name = "request_raisedby")
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name = "request_for")
    type = models.CharField(max_length=20, choices = requestTypeChoices, default='1')
    status = models.CharField(max_length=20, choices = requestStatusChoices, default='1')

class Document(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(default='', blank=True)

    def get_upload_path(instance, filename):
        return 'static/users/{0}/documents/{1}'.format(instance.user.username, filename)

    image = models.ImageField(upload_to=get_upload_path,blank=True)
    is_annotated = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

class Annotation(models.Model):
    name = models.CharField(max_length=255)
    topX = models.FloatField(default=0)
    topY = models.FloatField(default=0)
    bottomX = models.FloatField(default=0)
    bottomY = models.FloatField(default=0)
    is_antipattern = models.BooleanField(default=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE)

class AnnotationModel(models.Model):
    name = models.CharField(max_length=255)
    avgWidth = models.FloatField(default=0)
    avgHeight = models.FloatField(default=0)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def get_upload_path(instance, filename):
        return 'static/users/{0}/models/{1}'.format(instance.user.username, filename)

    model = models.FileField(upload_to=get_upload_path)
    model_pool = models.IntegerField()

class ModelPool(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(default='', blank=True)

    modelpool_list = models.ManyToManyField('self', blank = True, symmetrical=False, related_name='sub_modelpools')
    subdescription_list = models.TextField(default='', blank=True)
    pool_models = models.ManyToManyField(AnnotationModel, related_name='models', symmetrical=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="modelpool_user_set")

class ModelPoolStatus(models.Model):
    main_modelpool = models.ForeignKey(ModelPool, on_delete=models.CASCADE, related_name="main_modelpool")
    sub_modelpool = models.ForeignKey(ModelPool, on_delete=models.CASCADE, related_name="sub_modelpool")
    is_active = models.BooleanField(default=True)