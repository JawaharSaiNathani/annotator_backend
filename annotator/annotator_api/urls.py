from django.urls import path
from .views import *

urlpatterns = [
    path('register', RegisterView.as_view()),
    path('login', LoginView.as_view()),
    path('get-user', GetUserView.as_view()),
    path('get-user-list', GetUserListView.as_view(), name='UserList'),
    path('delete-annotator', AnnotatorView.as_view()),
    path('delete-project', ProjectView.as_view()),
    path('logout', LogoutView.as_view()),
    path('request-list', RequestView.as_view(), name='RequestList'),
    path('request-list/<int:pk>', RequestView.as_view(), name='RequestDetail'),
    path('user-document-list', UserDocumentListView.as_view(), name='UserDocumentList'),
    path('user-document-list/<int:pk>', UserDocumentListView.as_view(), name='UserDocumentDetail'),
    path('project-document-list', ProjectDocumentListView.as_view(), name='ProjectDocumentList'),
    path('project-document-list/<int:pk>', ProjectDocumentListView.as_view(), name='ProjectDocumentDetail'),
    path('document-annotation-list', AnnotationListView.as_view(), name='AnnotationList'),
    path('document-annotation-list/<int:pk>', AnnotationListView.as_view(), name='AnnotationDetail'),
    path('train-model', TrainModelView.as_view()),
    path('user-modelpool-list', ModelPoolListView.as_view(), name='ModelPoolList'),
    path('user-modelpool-list/<int:pk>', ModelPoolListView.as_view(), name='ModelPoolDetail'),
    path('change-modelpool-status', ModelPoolStatusView.as_view()),
]
