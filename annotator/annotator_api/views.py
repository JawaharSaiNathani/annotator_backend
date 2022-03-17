from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
import jwt
import datetime
import os
import sys
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from bson import ObjectId
from .serializers import *
from .models import *
# from .lookup import lookup



def get_user_from_request(request):
    token = request.headers['authtoken']
    if not token:
        raise AuthenticationFailed('Unauthenticated!')
    try:
        payload = jwt.decode(token, 'secret', algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        raise AuthenticationFailed('Unauthenticated!')

    user = User.objects.filter(_id=ObjectId(payload['_id'])).first() #doubt
    if not user:
        raise AuthenticationFailed('User not found')
    return user



class RegisterView(APIView):
    def post(self, request):
        data = request.data
        if ' ' in data['username']:
            return Response({
                'exception': 'username cannot contain spaces.'
            }, status=400)
        serializer = UserSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        user = User.objects.filter(username=data['username']).first()
        payload = {
            '_id': str(user._id),
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30),
            'iat': datetime.datetime.utcnow()
        }
        token = jwt.encode(payload, 'secret', algorithm='HS256').decode('utf8')
        response = Response()
        response.data = {
            'jwt': token
        }
        return response



class LoginView(APIView):
    def post(self, request):
        username = request.data['username']
        password = request.data['password']

        user = User.objects.filter(username=username).first()
        if user is None:
            raise AuthenticationFailed('User not found')
        if not user.check_password(password):
            raise AuthenticationFailed('Incorrect Password!')
        payload = {
            '_id': str(user._id),
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30),
            'iat': datetime.datetime.utcnow()
        }
        token = jwt.encode(payload, 'secret', algorithm='HS256').decode('utf8')
        response = Response()
        response.data = {
            'jwt': token
        }

        return response



class ValidateTokenView(APIView):
    def post(self, request):
        get_user_from_request(request)
        return Response({'message': 'success'})



class GetNotificationsView(APIView):
    def dispatch(self, request, *args, **kwargs):
        self.user = get_user_from_request(request)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        notifications = UserSerializer(self.user).get_user_notifications()
        return Response({
            'notifications': notifications
        })



class GetUserView(APIView):
    def dispatch(self, request, *args, **kwargs):
        self.user = get_user_from_request(request)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        data = UserSerializer(self.user).get_user_details()
        return Response(data)

    def put(self, request):
        serializer = UserSerializer(self.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'message': 'success'})



class GetUserProjectsView(APIView):
    def dispatch(self, request, *args, **kwargs):
        self.user = get_user_from_request(request)
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request):
        data = {}
        data['owned_projects'] = UserSerializer(self.user).get_user_owned_projects()
        data['shared_projects'] = UserSerializer(self.user).get_user_shared_projects()
        return Response(data)



class CreateProjectView(APIView):
    def dispatch(self, request, *args, **kwargs):
        self.user_id = get_user_from_request(request)._id
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request):
        data = request.data
        data['creator'] = ObjectId(self.user_id)
        data['owners'] = [ObjectId(self.user_id)]
        data['staff'] = []
        serializer = ProjectSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'message': 'project created successfully'})



class GetProjectUsersView(APIView):
    def dispatch(self, request, *args, **kwargs):
        self.user_id = get_user_from_request(request)._id
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request):
        proj_id = ObjectId(request.data['project_id'])
        proj_owners = ProjectSerializer(Project.objects.filter(_id=proj_id).first()).get_owners()
        proj_staff = ProjectSerializer(Project.objects.filter(_id=proj_id).first()).get_staff()

        if self.user_id in proj_owners or self.user_id in proj_staff:
            proj_data = ProjectSerializer(Project.objects.filter(_id=proj_id).first()).data
            proj_data['owners'] = []
            for owner in proj_owners:
                proj_data['owners'].append(UserSerializer(User.objects.filter(_id=owner).first()).get())
            
            proj_data['staff'] = []
            for staff in proj_staff:
                proj_data['staff'].append(UserSerializer(User.objects.filter(_id=staff).first()).get())

            return Response(proj_data)
        return Response({
            'exception': 'Project not found'
        }, status=203)



class GetRequestsView(APIView):
    def dispatch(self, request, *args, **kwargs):
        self.user_id = get_user_from_request(request)._id
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        data = request.data
        if data['terminal'] == 'user':
            if data['type'] == 'sent':
                return Response({
                    'requests': RequestSerializer(Request.objects.filter(user=self.user_id, terminal='1'), many=True).data
                })
            elif data['type'] == 'received':
                print(Request.objects.filter(user=self.user_id, terminal='2'))
                return Response({
                    'requests': RequestSerializer(Request.objects.filter(user=self.user_id, terminal='2'), many=True).data
                })
        elif data['terminal'] == 'project':
            if self.user_id in ProjectSerializer(Project.objects.filter(_id=ObjectId(data['project_id'])).first()).get_owners():
                if data['type'] == 'sent':
                    return Response({
                        'requests': RequestSerializer(Request.objects.filter(project=ObjectId(data['project_id']), terminal='2'), many=True).data
                    })
                elif data['type'] == 'received':
                    return Response({
                        'requests': RequestSerializer(Request.objects.filter(project=ObjectId(data['project_id']), terminal='1'), many=True).data
                    })
            else:
                return Response({
                    'exception': 'Access Denied'
                }, status=403)



class RequestView(APIView):
    def dispatch(self, request, *args, **kwargs):
        self.user = get_user_from_request(request)
        self.user_id = self.user._id
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        data = request.data
        if data['terminal'] == 'project':
            data['terminal'] = '2'
            data['project'] = ObjectId(data['project'])
            proj_owners = ProjectSerializer(Project.objects.filter(_id=data['project']).first()).get_owners()
            if self.user_id in proj_owners:
                data['user'] = User.objects.filter(username=data['user']).first()._id
                data['status'] = '1'
                serializer = RequestSerializer(data=data)
                serializer.is_valid(raise_exception=True)
                serializer.save()
            else:
                return Response({
                    'exception': "Access denied"
                }, status=403)
        else:
            data['terminal'] = '1'
            data['project'] = ObjectId(data['project'])
            data['user'] = self.user_id
            data['status'] = '1'
            serializer = RequestSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

        return Response({'message': 'success'})

    def put(self, request):
        if request.data['status'] == '2':
            req_id = request.data['id']
            req = Request.objects.filter(_id=ObjectId(req_id)).first()
            req_data = RequestSerializer(req).data

            is_user_valid = False
            if req_data['terminal'] == 'project':
                if req_data['user'] == UserSerializer(self.user).get():
                    is_user_valid = True
                    
            else:
                proj_id = req_data['project']['_id']
                proj_owners = ProjectSerializer(Project.objects.filter(_id=ObjectId(proj_id)).first()).get_owners()
                if self.user_id in proj_owners:
                    is_user_valid = True

            if is_user_valid == True:
                req_serializer = RequestSerializer(req, data={'status': '2'}, partial=True)
                req_serializer.is_valid(raise_exception=True)
                req_serializer.save()
                if req_data['role'] == 'owner':
                    proj_id = req_data['project']['_id']
                    proj_owners = ProjectSerializer(Project.objects.filter(_id=ObjectId(proj_id)).first()).get_owners()
                    if User.objects.filter(username=req_data['user']['username']).first()._id not in proj_owners:
                        proj_owners.append(User.objects.filter(username=req_data['user']['username']).first()._id)
                        proj_serializer = ProjectSerializer(Project.objects.filter(_id=ObjectId(proj_id)).first(), data={'owners': proj_owners}, partial=True)
                        proj_serializer.is_valid(raise_exception=True)
                        proj_serializer.save()
                else:
                    proj_id = req_data['project']['_id']
                    proj_staff = ProjectSerializer(Project.objects.filter(_id=ObjectId(proj_id)).first()).get_staff()
                    if User.objects.filter(username=req_data['user']['username']).first()._id not in proj_staff:
                        proj_staff.append(User.objects.filter(username=req_data['user']['username']).first()._id)
                        proj_serializer = ProjectSerializer(Project.objects.filter(_id=ObjectId(proj_id)).first(), data={'staff': proj_staff}, partial=True)
                        proj_serializer.is_valid(raise_exception=True)
                        proj_serializer.save()
            
                return Response({'message': 'success'})
            
            return Response({
                'exception': 'Request not found'
            }, status=400)
        else:
            req_id = request.data['id']
            req = Request.objects.filter(_id=ObjectId(req_id)).first()
            req_serializer = RequestSerializer(req, data={'status': '3'}, partial=True)
            req_serializer.is_valid(raise_exception=True)
            req_serializer.save()

            return Response({'message': 'success'})



class GetUserListView(APIView):
    def dispatch(self, request, *args, **kwargs):
        self.user = get_user_from_request(request)
        self.user_id = self.user._id
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        users = list(User.objects.all())
        users.remove(self.user)
        users_list = []
        for usr in users:
            if usr.is_staff == False:
                user_data = UserSerializer(usr).get()
                users_list.append(user_data)
        data = {'user-list': users_list}
        return Response(data)



class GetProjectListView(APIView):
    def dispatch(self, request, *args, **kwargs):
        self.user = get_user_from_request(request)
        self.user_id = self.user._id
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        projects = list(Project.objects.all())
        projects_list = []
        for proj in projects:
            proj_data = ProjectSerializer(proj).data
            projects_list.append(proj_data)

        data = {'project-list': projects_list}
        return Response(data)



def send_notification(title, description, user):
    notification = {
        'title': title,
        'description': description,
        'user': user
    }
    notif_serializer = NotificationSerializer(data=notification)
    notif_serializer.is_valid(raise_exception=True)
    notif_serializer.save()



class RemoveUserView(APIView):
    def dispatch(self, request, *args, **kwargs):
        self.user = get_user_from_request(request)
        self.user_id = self.user._id
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request):
        data = request.data
        proj_id = data['project_id']
        if data['user'] != ProjectSerializer(Project.objects.filter(_id=ObjectId(proj_id)).first()).data['creator']:
            proj_owners = ProjectSerializer(Project.objects.filter(_id=ObjectId(proj_id)).first()).get_owners()
            print(proj_owners)
            if self.user_id in proj_owners:
                temp_user_id = ObjectId(UserSerializer(User.objects.filter(username=data['user']).first()).data['_id'])
                print(proj_owners)
                if temp_user_id in proj_owners:
                    proj_owners.remove(temp_user_id)
                    proj_serializer = ProjectSerializer(Project.objects.filter(_id=ObjectId(proj_id)).first(), data={'owners': proj_owners}, partial=True)
                    proj_serializer.is_valid(raise_exception=True)
                    proj_serializer.save()
                    return Response({'message': 'success'})
                else:
                    proj_staff = ProjectSerializer(Project.objects.filter(_id=ObjectId(proj_id)).first()).get_staff()
                    if temp_user_id in proj_staff:
                        proj_staff.remove(temp_user_id)
                        proj_serializer = ProjectSerializer(Project.objects.filter(_id=ObjectId(proj_id)).first(), data={'staff': proj_staff}, partial=True)
                        proj_serializer.is_valid(raise_exception=True)
                        proj_serializer.save()
                        return Response({'message': 'success'})
                return Response({
                    'exception': 'User not found'
                }, status=203)
            return Response({
                'exception': 'No Permission'
            }, status=403)
        return Response({
            'exception': 'Creator cannot be removed from project.'
        }, status=203)



class LeaveProjectView(APIView):
    def dispatch(self, request, *args, **kwargs):
        self.user = get_user_from_request(request)
        self.user_id = self.user._id
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request):
        data = request.data
        proj_id = data['project_id']
        if self.user.username != ProjectSerializer(Project.objects.filter(_id=ObjectId(proj_id)).first()).data['creator']:
            proj_owners = ProjectSerializer(Project.objects.filter(_id=ObjectId(proj_id)).first()).get_owners()
            if self.user_id in proj_owners:
                proj_owners.remove(self.user_id)
                proj_serializer = ProjectSerializer(Project.objects.filter(_id=ObjectId(proj_id)).first(), data={'owners': proj_owners}, partial=True)
                proj_serializer.is_valid(raise_exception=True)
                proj_serializer.save()

                return Response({'message': 'success'})
            else:
                proj_staff = ProjectSerializer(Project.objects.filter(_id=ObjectId(proj_id)).first()).get_staff()
                if self.user_id in proj_staff:
                    proj_staff.remove(self.user_id)
                    proj_serializer = ProjectSerializer(Project.objects.filter(_id=ObjectId(proj_id)).first(), data={'staff': proj_staff}, partial=True)
                    proj_serializer.is_valid(raise_exception=True)
                    proj_serializer.save()

                    return Response({'message': 'success'})
                return Response({
                    'exception': 'Project not found'
                }, status=203)
        return Response({
            'exception': 'Creator cannot be removed from project.'
        }, status=203)



class DocumentView(APIView):
    def dispatch(self, request, *args, **kwargs):
        self.user_id = get_user_from_request(request)._id
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        data = dict(request.data)
        data['name'] = data['name'][0]
        data['description'] = data['description'][0]
        data['image'] = data['image'][0]
        data['project'] = ObjectId(data['project'][0])
        proj_owners = ProjectSerializer(Project.objects.filter(_id=data['project']).first()).get_owners()
        proj_staff = ProjectSerializer(Project.objects.filter(_id=data['project']).first()).get_staff()
        if self.user_id in proj_owners or self.user_id in proj_staff:
            serializer = DocumentSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        return Response({
            'exception': 'Access denied'
        }, status=403)

    def delete(self, request):
        data = request.data
        data['project'] = ObjectId(data['project'])
        proj_owners = ProjectSerializer(Project.objects.filter(_id=data['project']).first()).get_owners()
        proj_staff = ProjectSerializer(Project.objects.filter(_id=data['project']).first()).get_staff()
        if self.user_id in proj_owners or self.user_id in proj_staff:
            document = Document.objects.filter(_id=ObjectId(data['document'])).first()
            if not document:
                return Response({
                    'exception': 'Document not found'
                }, status=400)
            try:
                os.remove(str(document.image))
            except:
                print('[-] Document not found in storage')

            document.delete()
            return Response({'message': 'Success'})
        return Response({
            'exception': 'Access denied'
        }, status=403)



class DocumentDetailView(APIView):
    def dispatch(self, request, *args, **kwargs):
        self.user_id = get_user_from_request(request)._id
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request):
        data = request.data
        data['project'] = ObjectId(data['project'])
        project_serializer = ProjectSerializer(Project.objects.filter(_id=data['project']).first())
        proj_owners = project_serializer.get_owners()
        proj_staff = project_serializer.get_staff()
        if self.user_id in proj_owners or self.user_id in proj_staff:
            doc_data = DocumentSerializer(Document.objects.filter(_id=ObjectId(request.data['document'])).first()).data
            if doc_data['_id'] == None:
                return Response({
                    'exception': 'Document not found'
                }, status=400)
            return Response({
                'document': doc_data
            })
        return Response({
            'exception': 'Access Denied'
        }, status=403)



class DocumentListView(APIView):
    def dispatch(self, request, *args, **kwargs):
        self.user_id = get_user_from_request(request)._id
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        data = request.data
        data['project'] = ObjectId(data['project'])
        project = Project.objects.filter(_id=data['project']).first()
        if project:
            project_serializer = ProjectSerializer(project)
            proj_owners = project_serializer.get_owners()
            proj_staff = project_serializer.get_staff()
            if self.user_id in proj_owners or self.user_id in proj_staff:
                return Response(project_serializer.get_documents())
            return Response({
                'exception': 'Access Denied'
            }, status=403)
        else:
            return Response({
                'exception': 'Project cannot be found'
            }, status=400)



def validate_data(data, user_id):
    data['project'] = ObjectId(data['project'])
    print("validate_data")
    print(str(Document.objects.filter(_id=ObjectId(data['document'])).first().project))
    print(data['project'])
    # if Document.objects.filter(_id=ObjectId(data['document'])).first().project != data['project']:
    #     return Response({
    #         'exception': 'Document not found'
    #     }, status=400)

    project_serializer = ProjectSerializer(Project.objects.filter(_id=data['project']).first())
    proj_owners = project_serializer.get_owners()
    proj_staff = project_serializer.get_staff()
    if user_id in proj_owners or user_id in proj_staff:
        return True
    return Response({
        'exception': 'Access Denied'
    }, status=403)



class AnnotationView(APIView):
    def dispatch(self, request, *args, **kwargs):
        self.user_id = get_user_from_request(request)._id
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        resp = validate_data(request.data, self.user_id)
        if resp == True:
            data = request.data
            data['annotation']['document'] = ObjectId(data['annotation']['document'])
            data['annotation']['_id'] = ObjectId(data['annotation']['_id'])
            data['annotation']['user'] = self.user_id
            serializer = AnnotationSerializer(data=data['annotation'])
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'message': 'success'})
        return resp

    def put(self, request):
        resp = validate_data(request.data, self.user_id)
        if resp == True:
            data = request.data
            data['annotation']['document'] = ObjectId(data['annotation']['document'])
            data['annotation']['_id'] = ObjectId(data['annotation']['_id'])
            annotation = Annotation.objects.filter(_id=data['annotation']['_id'], document=data['annotation']['document']).first()
            if not annotation:
                return Response({
                    'exception': 'Annotation not found'
                }, status=400)
            if annotation.user == self.user_id:
                serializer = AnnotationSerializer(annotation, data=data['annotation'], partial=True)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response({'message': 'success'})
            return Response({
                'exception': 'Access Denied'
            }, status=403)
        return resp

    def delete(self, request):
        resp = validate_data(request.data, self.user_id)
        if resp == True:
            data = request.data
            data['annotation']['document'] = ObjectId(data['annotation']['document'])
            data['annotation']['_id'] = ObjectId(data['annotation']['_id'])
            annotation = Annotation.objects.filter(_id=data['annotation']['_id'], document=data['annotation']['document']).first()
            if not annotation:
                return Response({
                    'exception': 'Annotation not found'
                }, status=400)
            if annotation.user == self.user_id:
                annotation.delete()
                return Response({'message': 'success'})
            return Response({
                'exception': 'Access Denied'
            }, status=403)
        return resp



class AnnotationListView(APIView):
    def dispatch(self, request, *args, **kwargs):
        self.user_id = get_user_from_request(request)._id
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        resp = validate_data(request.data, self.user_id)
        if resp == True:
            data = request.data
            data['document'] = ObjectId(data['document'])
            annotations = DocumentSerializer(Document.objects.filter(_id=data['document']).first()).get_annotations()
            user_annotations = []
            other_annotations = []
            for annotation in annotations:
                if annotation['user'] == self.user_id:
                    user_annotations.append(annotation)
                else:
                    other_annotations.append(annotation)
            return Response({
                'user_annotations': user_annotations,
                'other_annotations': other_annotations
            })
        return resp

class AllAnnotationsView(APIView):
    def dispatch(self, request, *args, **kwargs):
        self.user_id = get_user_from_request(request)._id
        return super().dispatch(request, *args, **kwargs)
    
    def post(self,request):
        print("AllAnnotationsView Started")
        data = request.data
        print(data)
        data['project'] = ObjectId(data['project'])
        project_serializer = ProjectSerializer(Project.objects.filter(_id=data['project']).first())
        proj_owners = project_serializer.get_owners()
        proj_staff = project_serializer.get_staff()

        if self.user_id in proj_owners or self.user_id in proj_staff:
            annotations = []
            
            for document in Document.objects.filter(project=data['project']):
                print("hello")
                for annotation in Annotation.objects.filter(document=document._id):

                    annotations.append({
                        'name':annotation.name,
                        '_id': str(annotation._id),
                        'topX': annotation.topX,
                        'topY': annotation.topY,
                        'bottomX': annotation.bottomX,
                        'bottomY': annotation.bottomY,
                        'is_antipattern': annotation.is_antipattern,
                        'document': str(document._id)
                    })
            return Response({
                "annotations":annotations
            })
        
        return Response({
        'exception': 'Access Denied'
    }, status=403)

            

class TrainModelView(APIView):
    def dispatch(self, request, *args, **kwargs):
        self.user_id = get_user_from_request(request)._id
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        data = request.data
        data['project'] = ObjectId(data['project'])
        project_serializer = ProjectSerializer(Project.objects.filter(_id=data['project']).first())
        proj_owners = project_serializer.get_owners()
        proj_staff = project_serializer.get_staff()

        if self.user_id in proj_owners or self.user_id in proj_staff:
            model_name = data['model_name']
            annotations = []
            pattern_count = 0
            for document in Document.objects.filter(project=data['project']):
                for annotation in Annotation.objects.filter(name=model_name, document=document._id):
                    if annotation.is_antipattern == False:
                        pattern_count += 1
                    annotations.append({
                        'topX': annotation.topX,
                        'topY': annotation.topY,
                        'bottomX': annotation.bottomX,
                        'bottomY': annotation.bottomY,
                        'is_antipattern': annotation.is_antipattern,
                        'document': document.image
                    })

            if pattern_count < 1:
                return Response({
                    'message': 'Annotations not found for model - ' + model_name
                }, status=203)

            # result, dimensions = lookup(annotations, model_name, channel_layer)
            result = False
            dimensions = [0, 0]
            if result:
                with open('static/trained_models/' + model_name + '.pth', 'rb') as f:
                    model_bytestream = BytesIO(f.read())

                # os.remove('static/trained_models/' + model_name + '.pth')

                model = InMemoryUploadedFile(
                    model_bytestream, 'FileFeild', model_name+'.pth', 'pth', sys.getsizeof(model_bytestream), None)
                data = {
                    'name': model_name,
                    'avgWidth': dimensions[1],
                    'avgHeight': dimensions[0],
                    'model': model,
                    'user': self.user_id
                }
                modelpool_data = {
                    'name': model_name,
                    'user': self.user_id
                }

                annotation_model = AnnotationModel.objects.filter(
                    name=model_name, user=self.user_id).first()

                if 'description' in request.data:
                    modelpool_data['description'] = request.data['description']
                    modelpool_data['subdescription_list'] = request.data['description']

                if annotation_model:
                    modelpool = ModelPool.objects.filter(
                        id=annotation_model.model_pool).first()
                    modelpool_serializer = ModelPoolSerializer(
                        modelpool, data=modelpool_data, partial=True)

                else:
                    modelpool_data['modelpool_list'] = []
                    modelpool_data['pool_models'] = []
                    modelpool_serializer = ModelPoolSerializer(data=modelpool_data)

                modelpool_serializer.is_valid(raise_exception=True)
                modelpool_serializer.save()

                if annotation_model:
                    try:
                        os.remove(str(annotation_model.model))
                    except:
                        print('[-] Model not found in storage')

                    serializer = AnnotationModelSerializer(
                        annotation_model, data=data, partial=True)

                else:
                    data['model_pool'] = modelpool_serializer.data['id']
                    serializer = AnnotationModelSerializer(data=data)

                serializer.is_valid(raise_exception=True)
                serializer.save()

                if not annotation_model:
                    modelpool = ModelPool.objects.filter(
                        id=serializer.data['model_pool']).first()
                    modelpool_serializer = ModelPoolSerializer(
                        modelpool, data={'pool_models': [serializer.data['id']]}, partial=True)
                    modelpool_serializer.is_valid(raise_exception=True)
                    modelpool_serializer.save()
                return Response({'message': 'Model successfully trained'})

            else:
                return Response({
                    'message': 'Model cannot be trained'
                }, status=403)


def get_pool_models(modelpool_id):
    pool_models = []
    modelpool = ModelPool.objects.filter(id=modelpool_id).first()
    if modelpool:
        data = ModelPoolSerializer(modelpool).data
        for pool in data['modelpool_list']:
            modelpool_status = ModelPoolStatus.objects.filter(
                main_modelpool=modelpool_id, sub_modelpool=pool).first()
            if modelpool_status.is_active == True:
                subpool_models = get_pool_models(pool)
                pool_models = pool_models + subpool_models
        if len(data['modelpool_list']) == 0:
            pool_models.append(data['pool_models'][0])
    return list(set(pool_models))


def get_modelpool(modelpool_id, models_required=True):
    modelpool = ModelPool.objects.filter(id=modelpool_id).first()

    if modelpool:
        data = ModelPoolSerializer(modelpool).data
        del data['user']
        sub_modelpools_data = []
        for pool in data['modelpool_list']:
            sub_modelpool = ModelPool.objects.filter(id=pool).first()
            sub_modelpool_status = ModelPoolStatus.objects.filter(
                main_modelpool=modelpool.id, sub_modelpool=sub_modelpool.id).first().is_active
            sub_modelpools_data.append({
                'id': sub_modelpool.id,
                'name': sub_modelpool.name,
                'is_active': sub_modelpool_status
            })
        data['modelpool_list'] = sub_modelpools_data
        del data['pool_models']
        if models_required:
            pool_models = get_pool_models(data['id'])
            models_data = []
            for model_id in pool_models:
                annotation_model = AnnotationModel.objects.filter(
                    id=model_id).first()
                models_data.append({
                    'id': annotation_model.id,
                    'name': annotation_model.name
                })
            data['pool_models'] = models_data
        return data

    return False


class ModelPoolListView(APIView):
    def get(self, request):
        get_user_from_request(request)
        user_id = request.data['id']

        if 'pk' in self.kwargs:
            data = get_modelpool(self.kwargs['pk'])
            if data != False:
                return Response(data)
            else:
                return Response({
                    'message': 'ModelPool not found'
                }, status=400)

        modelpools = ModelPool.objects.filter(user=user_id)
        modelpools_data = []
        for modelpool in modelpools:
            modelpools_data.append(get_modelpool(modelpool.id, False))

        return Response(modelpools_data)

    def post(self, request):
        get_user_from_request(request)
        user_id = request.data['id']
        data = request.data
        data['pool_models'] = []
        data['user'] = user_id
        serializer = ModelPoolSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        pool_models = []
        description = ""
        for pool in data['modelpool_list']:
            pool_models += get_pool_models(pool)
            desc = ModelPool.objects.filter(
                id=pool).first().subdescription_list
            if desc != '':
                description += desc.replace(';', '') + ";"

            modelpool_status_data = {
                'main_modelpool': serializer.data['id'],
                'sub_modelpool': pool
            }
            modelpool_status_serializer = ModelPoolStatusSerializer(
                data=modelpool_status_data)
            modelpool_status_serializer.is_valid(raise_exception=True)
            modelpool_status_serializer.save()

        modelpool = ModelPool.objects.filter(id=serializer.data['id']).first()
        serializer = ModelPoolSerializer(modelpool, data={
                                         'pool_models': pool_models, 'subdescription_list': description}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'message': 'success'})


class ModelPoolStatusView(APIView):
    def post(self, request):
        get_user_from_request(request)
        main_modelpool, sub_modelpool = request.data['main_modelpool'], request.data['sub_modelpool']
        modelpool_status = ModelPoolStatus.objects.filter(
            main_modelpool=main_modelpool, sub_modelpool=sub_modelpool).first()
        serializer = ModelPoolStatusSerializer(
            modelpool_status, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'success'})
