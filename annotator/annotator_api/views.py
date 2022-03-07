from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
import jwt
import datetime
import base64
import os
import sys
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
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

    user = User.objects.filter(id=payload['id']).first()
    if not user:
        raise AuthenticationFailed('User not found')
    print("########inside get_user_from_request############")
    print(user)
    return user


class RegisterView(APIView):
    def post(self, request):
        data = request.data
        print(data)
        serializer = UserSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        user = User.objects.filter(username=data['username']).first()
        payload = {
            'id': user.id,
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
            'id': user.id,
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
        token = request.data['token']
        if not token:
            raise AuthenticationFailed('Unauthenticated!')

        try:
            payload = jwt.decode(token, 'secret', algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Unauthenticated!')

        user = User.objects.filter(id=payload['id']).first()
        if not user:
            raise AuthenticationFailed('User not found')

        return Response({'message': 'success'})


class GetNotificationsView(APIView):
    def get(self, request):
        user = get_user_from_request(request)
        notifications = NotificationSerializer(
            Notification.objects.filter(user=user.id), many=True).data
        return Response({
            'notifications': notifications
        })


class GetUserView(APIView):
    def get(self, request):
        user = get_user_from_request(request)
        data = UserSerializer(user).data
        if data['image'] != None:
            image = open(data['image'], 'rb')
            del data['image']
            data['image'] = base64.b64encode(image.read())
        else:
            data['image'] = ''

        annotator_list = []
        for annotator in data['annotator_list']:
            annotator_data = UserSerializer(
                User.objects.filter(id=annotator).first()).data
            del annotator_data['annotator_list']
            del annotator_data['project_list']
            annotator_list.append(annotator_data)

        project_list = []
        for project in data['project_list']:
            project_data = UserSerializer(
                User.objects.filter(id=project).first()).data
            del project_data['annotator_list']
            del project_data['project_list']
            project_list.append(project_data)

        data['annotator_list'] = annotator_list
        data['project_list'] = project_list

        return Response(data)

    def put(self, request):
        user = get_user_from_request(request)
        serializer = UserSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'message': 'success'})

class GetSentRequests(APIView):
    def get(self, request):
        user = get_user_from_request(request)
        data = {}
        sent_requests = RequestSerializer(Request.objects.filter(from_user=user.id), many=True).data
        request_type = {'1': 'work', '2': 'hire'}
        request_status = {'1': 'pending', '2': 'accepted', '3': 'declined'}
        for request in sent_requests:
            request['type'] = request_type[request['type']]
            request['status'] = request_status[request['status']]
        data['sent-requests'] = sent_requests
        return Response(data)

class GetReceivedRequests(APIView):
    def get(self, request):
        user = get_user_from_request(request)
        data = {}
        received_requests = RequestSerializer(Request.objects.filter(to_user=user.id), many=True).data
        request_type = {'1': 'work', '2': 'hire'}
        request_status = {'1': 'pending', '2': 'accepted', '3': 'declined'}
        for request in received_requests:
            request['type'] = request_type[request['type']]
            request['status'] = request_status[request['status']]
        data['received-requests'] = received_requests
        return Response(data)

class GetUserListView(APIView):
    def get(self, request):
        user = get_user_from_request(request)
        users = list(User.objects.all())
        users.remove(user)
        users_list = []
        for usr in users:
            if usr.is_staff == False:
                user_data = UserSerializer(usr).data
                del user_data['annotator_list']
                del user_data['project_list']
                users_list.append(user_data)
        data = {'user-list': users_list}
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


class AnnotatorView(APIView):
    def delete(self, request, pk):
        user = get_user_from_request(request)
        annotator_id = pk

        annotator_list = UserSerializer(user).data['annotator_list']
        annotator_list.remove(annotator_id)
        serializer = UserSerializer(
            user, data={'annotator_list': annotator_list}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        annotator = User.objects.filter(id=annotator_id).first()
        annotator_project_list = UserSerializer(annotator).data['project_list']
        annotator_project_list.remove(user.id)
        annotator_serializer = UserSerializer(
            annotator, data={'project_list': annotator_project_list}, partial=True)
        annotator_serializer.is_valid(raise_exception=True)
        annotator_serializer.save()

        send_notification(
            'From ' + user.name, 'You have been removed from the project of the user ' + user.name, annotator_id)

        return Response({'message': 'success'})

class ProjectView(APIView):
    def delete(self, request, pk):
        user = get_user_from_request(request)
        project_id = pk

        user_project_list = UserSerializer(user).data['project_list']
        user_project_list.remove(project_id)
        serializer = UserSerializer(
            user, data={'project_list': user_project_list}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        project = User.objects.filter(id=project_id).first()
        project_annotator_list = UserSerializer(project).data['annotator_list']
        project_annotator_list.remove(user.id)
        project_serializer = UserSerializer(
            project, data={'annotator_list': project_annotator_list}, partial=True)
        project_serializer.is_valid(raise_exception=True)
        project_serializer.save()

        send_notification('From ' + user.name, user.name +
                          ' no longer works as annotator for you', project_id)

        return Response({'message': 'success'})


class RequestView(APIView):
    def post(self, request):
        user = get_user_from_request(request)
        data = request.data
        data['from_user'] = user.id
        data['status'] = '1'
        serializer = RequestSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'message': 'success'})

    def put(self, request, pk):
        get_user_from_request(request)
        req_data = request.data
        req = Request.objects.filter(id=pk).first()
        req_serializer = RequestSerializer(req, data=req_data, partial=True)
        req_serializer.is_valid(raise_exception=True)
        req_serializer.save()

        data = RequestSerializer(req).data

        from_user = User.objects.filter(id=data['from_user']).first()
        from_user_data = UserSerializer(from_user).data
        to_user = User.objects.filter(id=data['to_user']).first()
        to_user_data = UserSerializer(to_user).data
        if data['status'] == '2':
            if from_user_data['id'] not in to_user_data['annotator_list']:
                if data['type'] == '1':
                    to_user_data['annotator_list'].append(from_user_data['id'])
                    from_user_data['project_list'].append(to_user_data['id'])
                    send_notification('From ' + to_user.name, 'Your request to work as annotator for ' +
                                      to_user.name + ' has been accepted', from_user.id)
                else:
                    to_user_data['project_list'].append(from_user_data['id'])
                    from_user_data['annotator_list'].append(to_user_data['id'])
                    send_notification('From ' + to_user.name, 'Your request to hire ' +
                                      to_user.name + ' as annotator has been accepted', from_user.id)
                del from_user_data['image']
                from_user_serializer = UserSerializer(
                    from_user, data=from_user_data, partial=True)
                from_user_serializer.is_valid(raise_exception=True)
                from_user_serializer.save()
                
                del to_user_data['image']
                to_user_serializer = UserSerializer(
                    to_user, data=to_user_data, partial=True)
                to_user_serializer.is_valid(raise_exception=True)
                to_user_serializer.save()
        else:
            send_notification('From ' + to_user.name,
                              'Your request has been declined', from_user.id)

        return Response({'message': 'success'})


def get_single_Document(id):
    document = Document.objects.filter(id=id).first()

    if not document:
        return Response({
            'exception': 'Document not found'
        }, status=400)

    serializer = DocumentSerializer(document)
    data = serializer.data
    try:
        image = open(data['image'], 'rb')
        del data['image']
        del data['user']
        data['image'] = base64.b64encode(image.read())
        return Response(data)
    except:
        document.delete()
        return Response({
            'exception': 'Document not found'
        }, status=400)


def get_multiple_documents(user_id):
    print("#########inside get_multiple_documents###########")
    print(user_id)
    documents = []
    for document in Document.objects.filter(user=user_id):
        serializer = DocumentSerializer(document)
        data = serializer.data
        try:
            # image = open(data['image'], 'rb')
            # del data['image']
            # del data['user']
            # data['image'] = base64.b64encode(image.read())
            documents.append(data)
        except:
            document.delete()
            print('[-] Document not found in storage')
    response = Response()
    response.data = documents
    return response


class UserDocumentListView(APIView):
    def get(self, request, **kwargs):
        user = get_user_from_request(request)

        if 'pk' in self.kwargs:
            doc_id = self.kwargs['pk']
            if doc_id in Document.objects.filter(user=user.id).values_list('id', flat=True):
                return get_single_Document(self.kwargs['pk'])
            return Response({
                'exception': 'Document not found'
            }, status=400)

        else:
            return get_multiple_documents(user.id)

    def post(self, request):
        data = request.data
        user_id = get_user_from_request(request).id
        data['user'] = user_id
        serializer = DocumentSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def put(self, request, pk):
        get_user_from_request(request)
        document = Document.objects.filter(id=pk).first()
        if not document:
            return Response({
                'message': 'Document not found'
            }, status=400)
        serializer = DocumentSerializer(
            document, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'message': 'success'})

    def delete(self, request, pk):
        get_user_from_request(request)
        document = Document.objects.filter(id=pk).first()

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


class ProjectDocumentListView(APIView):
    def get(self, request, **kwargs):
        user = get_user_from_request(request)

        project_id = request.data['project_id']
        if project_id in User.objects.filter(id=user.id).values_list('project_list', flat=True):
            if 'pk' in self.kwargs:
                doc_id = self.kwargs['pk']
                if doc_id in Document.objects.filter(user=project_id).values_list('id', flat=True):
                    return get_single_Document(self.kwargs['pk'])
                return Response({
                    'exception': 'Document not found'
                }, status=400)

            else:
                return get_multiple_documents(project_id)

        return Response({
            'exception': 'Project Not Found'
        }, status=400)


class AnnotationListView(APIView):
    def get(self, request):
        get_user_from_request(request)
        annotations = []
        for obj in Annotation.objects.filter(document=request.data['document']):
            serializer = AnnotationSerializer(obj)
            data = serializer.data
            del data['document']
            annotations.append(data)
        response = Response()
        response.data = annotations
        return response

    def post(self, request):
        get_user_from_request(request)
        serializer = AnnotationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def put(self, request, pk):
        get_user_from_request(request)
        annotation = Annotation.objects.filter(id=pk).first()
        if not annotation:
            return Response({
                'message': 'Annotation not found'
            }, status=400)
        serializer = AnnotationSerializer(
            annotation, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        get_user_from_request(request)
        annotation = Annotation.objects.filter(id=pk).first()

        if not annotation:
            return Response({
                'exception': 'Annotation not found'
            }, status=400)

        annotation.delete()
        return Response({'message': 'Success'})


class TrainModelView(APIView):
    def post(self, request):
        get_user_from_request(request)
        user_id = request.data['id']
        model_name = request.data['model_name']

        annotations = []
        pattern_count = 0
        for document in Document.objects.filter(user=user_id):
            for annotation in Annotation.objects.filter(name=model_name, document=document.id):
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
                'message': 'Annotations not found for model ' + model_name
            }, status=400)

        # result, dimensions = lookup(annotations, model_name)
        result = True
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
                'user': user_id
            }
            modelpool_data = {
                'name': model_name,
                'user': user_id
            }

            annotation_model = AnnotationModel.objects.filter(
                name=model_name, user=user_id).first()

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
            }, status=400)


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
    def get(self, request, **kwargs):
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
