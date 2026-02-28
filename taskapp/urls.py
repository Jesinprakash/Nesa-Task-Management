from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.urls import path

from taskapp import views

urlpatterns = [

    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),

    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('dashboard/',views.dashboard,name='adminpanel'),

    path('',views.LoginView.as_view(),name='login'),

    path('admin/create/', views.CreateAdminView.as_view(), name='create_admin'),

    path("create-user/", views.CreateUserView.as_view(), name="create_user"),

    path("update-admin/<int:pk>/", views.UpdateAdminView.as_view(), name="update_admin"),

    path("delete-admin/<int:pk>/", views.DeleteAdminView.as_view(), name="delete_admin"),

    path('user/<int:pk>/update/',views.UpdateUserView.as_view(),name="update_user"),

    path('user/<int:pk>/delete/',views.DeleteUserView.as_view(),name='delete_user'),

    path('tasks/create/', views.TaskCreateAPIView.as_view()),

    path('tasks/',views.UserTaskListView.as_view()),

    path('tasks/<int:pk>/',views.TaskUpdateApiView.as_view()),

    path('tasks/<int:pk>/report/',views.TaskReportView.as_view()),

    path('task/<int:pk>/update/',views.TaskUpdateView.as_view(),name='task_update'),

    path('task/<int:pk>/delete/',views.TaskDeleteView.as_view(),name='task_delete'),

    path('logout/',views.logout_view,name="logout")

]
