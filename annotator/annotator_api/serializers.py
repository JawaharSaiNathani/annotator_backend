from typing_extensions import Required
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import *

class UserSerializer(serializers.ModelSerializer):
    annotator_list = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True, required=False)
    project_list = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True, required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'name', 'description', 'annotator_list', "project_list"]
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance

class NotificationSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=False)

    class Meta:
        model = Notification
        fields = ['id', 'title', 'description', 'user']

class RequestSerializer(serializers.ModelSerializer):
    from_user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=False)
    to_user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=False)

    class Meta:
        model = Request
        fields = ['id', 'title', 'description', 'from_user', 'to_user', 'type', 'status']

class DocumentSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=False)

    class Meta:
        model = Document
        fields = ['id', 'name', 'description', 'image', 'is_annotated', 'user']

class AnnotationSerializer(serializers.ModelSerializer):
    document = serializers.PrimaryKeyRelatedField(queryset=Document.objects.all(), many=False)

    class Meta:
        model = Annotation
        fields = ['id', 'name', 'topX', 'topY', 'bottomX', 'bottomY', 'is_antipattern', 'document']

class AnnotationModelSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=False)

    class Meta:
        model = AnnotationModel
        fields = ['id', 'name', 'avgWidth', 'avgHeight', 'model', 'user', 'model_pool']

class ModelPoolSerializer(serializers.ModelSerializer):
    pool_models = serializers.PrimaryKeyRelatedField(queryset=AnnotationModel.objects.all(), many=True)
    modelpool_list = serializers.PrimaryKeyRelatedField(queryset=ModelPool.objects.all(), many=True)
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=False)

    class Meta:
        model = ModelPool
        fields = ['id', 'name', 'description', 'modelpool_list', 'subdescription_list', 'pool_models', 'user']

class ModelPoolStatusSerializer(serializers.ModelSerializer):
    main_modelpool = serializers.PrimaryKeyRelatedField(queryset=ModelPool.objects.all(), many=False)
    sub_modelpool = serializers.PrimaryKeyRelatedField(queryset=ModelPool.objects.all(), many=False)

    class Meta:
        model = ModelPoolStatus
        fields = ['id', 'main_modelpool', 'sub_modelpool', 'is_active']