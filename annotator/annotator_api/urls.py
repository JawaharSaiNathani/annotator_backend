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

    path('get-project-users', GetProjectUsersView.as_view()),

    path('delete-user', RemoveUserView.as_view()),
    path('leave-project', LeaveProjectView.as_view()),
    
    path('request-list', RequestView.as_view(), name='RequestList'),

    path('documents', DocumentView.as_view(), name='Document'),

    path('document-list', DocumentListView.as_view(), name='DocumentList'),
    path('document-detail', DocumentDetailView.as_view(), name='DocumentDetail'),

    path('annotation', AnnotationView.as_view(), name='Annotation'),
    path('annotation-list', AnnotationListView.as_view(), name='AnnotationList'),
    path('all-annotations',AllAnnotationsView.as_view(), name="AllAnnotations"),

    path('train-model', TrainModelView.as_view()),
    path('annotate', AnnotateView.as_view()),

    path('modelpool-list', ModelPoolListView.as_view(), name='ModelPoolList'),
    path('create-modelpool', ModelPoolView.as_view()),
    path('change-modelpool-status', ModelPoolStatusView.as_view()),
]
