from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(User)
admin.site.register(Project)
admin.site.register(Notification)
admin.site.register(Document)
admin.site.register(Annotation)
admin.site.register(ModelPool)
admin.site.register(AnnotationModel)
admin.site.register(ModelPoolStatus)
admin.site.register(Request)
