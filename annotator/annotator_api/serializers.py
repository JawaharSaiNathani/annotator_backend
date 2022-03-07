from numpy import source
from rest_framework import serializers
import base64
from .models import *
from bson import ObjectId



class AnnotationSerializer(serializers.ModelSerializer):
    _id = ObjectId()
    document = serializers.PrimaryKeyRelatedField(queryset=Document.objects.all(), many=False)

    class Meta:
        model = Annotation
        fields = ['_id', 'name', 'topX', 'topY', 'bottomX', 'bottomY', 'is_antipattern', 'document']
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        return {
            '_id': str(data['_id']),
            'name': data['name'],
            'topX': data['topX'],
            'topY': data['topY'],
            'bottomX': data['bottomX'],
            'bottomY': data['bottomY'],
            'is_antipattern': data['is_antipattern']
        }


class DocumentSerializer(serializers.ModelSerializer):
    _id = ObjectId()
    project = serializers.PrimaryKeyRelatedField(queryset=Project.objects.all(), many=False)

    annotation_list = AnnotationSerializer(source="annotations", required=False, Many=True)

    class Meta:
        model = Document
        fields = ['_id', 'name', 'description', 'image', 'is_annotated', 'project', 'annotation_list']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        try:
            image = open(data['image'], 'rb')
            data['image'] = base64.b64encode(image.read())
        except:
            instance.delete()
        return {
            '_id': str(data['_id']),
            'name': data['name'],
            'description': data['description'],
            'image': data['image'],
            'is_annotated': data['is_annotated']
        }
    
    def get_annotations(self):
        data = super().to_representation(self.instance)
        return data['annotation_list']



class ProjectSerializer(serializers.ModelSerializer):
    _id = ObjectId()
    owners = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True)
    staff = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True, required=False)

    project_documents = DocumentSerializer(source='documents', required=False, many=True)

    class Meta:
        model = Project
        fields = ['_id', 'title', 'description', 'owners', 'staff', 'project_documents']
    
    def to_representation(self, instance):
        return {
            '_id': str(instance._id),
            'title': instance.title,
            'description': instance.description
        }

    def get_owners(self):
        data = super().to_representation(self.instance)
        return data['owners']
    
    def get_staff(self):
        data = super().to_representation(self.instance)
        return data['staff']
    
    def get_documents(self):
        data = super().to_representation(self.instance)
        return data['project_documents']



class NotificationSerializer(serializers.ModelSerializer):
    _id = ObjectId()
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=False)

    class Meta:
        model = Notification
        fields = ['_id', 'title', 'description', 'user']

    def to_representation(self, instance):
        return {
            '_id': str(instance._id),
            'title': instance.title,
            'description': instance.description
        }



class UserSerializer(serializers.ModelSerializer):
    _id = ObjectId()
    owned_projects = ProjectSerializer(source='owner', required=False, many=True)
    shared_projects = ProjectSerializer(source='staff', required=False, many=True)

    notifications = NotificationSerializer(source='user_notifications', required=False, many=True)

    class Meta:
        model = User
        fields = ['_id', 'username', 'password', 'name', 'description', 'image', 'owned_projects', 'shared_projects', 'notifications']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['_id'] = str(data['_id'])
        return data

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance
    
    def get(self):
        return {
            'username': self.instance.username,
            'name': self.instance.name
        }

    def get_user_details(self):
        img = str(self.instance.image)
        if img != '':
            image = open(img, 'rb')
            img = base64.b64encode(image.read())
        return {
            'username': self.instance.username,
            'name': self.instance.name,
            'description': self.instance.description,
            'image': img
        }

    def get_user_owned_projects(self):
        data = dict(self.to_representation(self.instance))
        return data['owned_projects']
    
    def get_user_shared_projects(self):
        data = dict(self.to_representation(self.instance))
        return data['shared_projects']

    def get_user_notifications(self):
        data = dict(self.to_representation(self.instance))
        return data['notifications']



class RequestSerializer(serializers.ModelSerializer):
    _id = ObjectId()
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=False)
    project = serializers.PrimaryKeyRelatedField(queryset=Project.objects.all(), many=False)

    class Meta:
        model = Request
        fields = ['_id', 'title', 'description', 'user', 'project', 'role', 'terminal', 'status']
    
    def to_representation(self, instance):
        role = {'1': 'owner', '2': 'staff'}
        terminal = {'1': 'user', '2': 'project'}
        status = {'1': 'pending', '2': 'accepted', '3': 'declined'}
        return {
            '_id': str(instance._id),
            'title': instance.title,
            'description': instance.description,
            'user': UserSerializer(User.objects.filter(_id=instance.user._id).first()).get(),
            'project': ProjectSerializer(Project.objects.filter(_id=instance.project._id).first()).data,
            'role': role[instance.role],
            'terminal': terminal[instance.terminal],
            'status': status[instance.status]
        }



class AnnotationModelSerializer(serializers.ModelSerializer):
    _id = ObjectId()
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=False)

    class Meta:
        model = AnnotationModel
        fields = ['_id', 'name', 'avgWidth', 'avgHeight', 'model', 'user', 'model_pool']

class ModelPoolSerializer(serializers.ModelSerializer):
    _id = ObjectId()
    pool_models = serializers.PrimaryKeyRelatedField(queryset=AnnotationModel.objects.all(), many=True)
    modelpool_list = serializers.PrimaryKeyRelatedField(queryset=ModelPool.objects.all(), many=True)
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=False)

    class Meta:
        model = ModelPool
        fields = ['_id', 'name', 'description', 'modelpool_list', 'subdescription_list', 'pool_models', 'user']

class ModelPoolStatusSerializer(serializers.ModelSerializer):
    _id = ObjectId()
    main_modelpool = serializers.PrimaryKeyRelatedField(queryset=ModelPool.objects.all(), many=False)
    sub_modelpool = serializers.PrimaryKeyRelatedField(queryset=ModelPool.objects.all(), many=False)

    class Meta:
        model = ModelPoolStatus
        fields = ['_id', 'main_modelpool', 'sub_modelpool', 'is_active']