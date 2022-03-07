from django.urls import path
from .views import *

urlpatterns = [
    path('register', RegisterView.as_view()),
    path('login', LoginView.as_view()),

     path('validate-token', ValidateTokenView.as_view()),
    path('get-notifications', GetNotificationsView.as_view()),

    path('get-user', GetUserView.as_view()),
    path('get-user-projects', GetUserProjectsView.as_view()),

    path('create-project', CreateProjectView.as_view()),

    path('get-requests', GetRequestsView.as_view()),
    path('get-user-list', GetUserListView.as_view(), name='UserList'),
    path('get-project-list', GetProjectListView.as_view(), name='ProjectList'),

    path('get-project', GetProjectView.as_view()),

    path('delete-user', RemoveUserView.as_view()),
    path('leave-project', LeaveProjectView.as_view()),
    
    path('request-list', RequestView.as_view(), name='RequestList'),

    path('documents', DocumentView.as_view(), name='Document'),

    path('document-list', DocumentListView.as_view(), name='DocumentList'),
    path('document-detail', DocumentDetailView.as_view(), name='DocumentDetail'),

    path('annotation', AnnotationView.as_view(), name='Annotation'),
    path('annotation/<int:pk>',AnnotationView.as_view(), name='AnnotationDetail'),
    path('annotation-list', AnnotationListView.as_view(), name='AnnotationList'),

    path('train-model', TrainModelView.as_view()),
    path('user-modelpool-list', ModelPoolListView.as_view(), name='ModelPoolList'),
    path('user-modelpool-list/<int:pk>',
         ModelPoolListView.as_view(), name='ModelPoolDetail'),
    path('change-modelpool-status', ModelPoolStatusView.as_view()),
]
