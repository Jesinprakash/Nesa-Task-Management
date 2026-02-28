from django.shortcuts import render

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from taskapp.models import Task, User
from taskapp.serializers import TaskSerializer,CreateTaskSerializer
from taskapp.permissions import IsAdminOrSuperAdmin
from django.views import View
from django.contrib.auth import authenticate, login,logout
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework import authentication

from rest_framework import status

from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.hashers import make_password
from django.contrib import messages

class LoginView(View):

    def get(self, request):

        return render(request, "login.html")

    def post(self, request):
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            if user.role == "SUPERADMIN":
                return redirect("adminpanel")
            # elif user.role == "ADMIN":
            #     return redirect("adminpanel")
            # else:
            #     return redirect("adminpanel")

        return render(request, "login.html", {
            "error": "Invalid credentials"
        })



@login_required
def dashboard(request):

    if request.user.role == "SUPERADMIN":

        # Admins created by this superadmin
        admins = User.objects.filter(
            role="ADMIN",
            created_by=request.user
        )

        # Users under those admins
        users = User.objects.filter(
            role="USER",
            assigned_admin__in=admins
        )

        # Tasks created by this superadmin
        tasks = Task.objects.filter(
            created_by=request.user
        )

        return render(
            request,
            "superadmin_dashboard.html",
            {
                "admins": admins,
                "users": users,
                "tasks": tasks
            }
        )

    elif request.user.role == "ADMIN":

        users = User.objects.filter(
            role="USER",
            assigned_admin=request.user
        )

        return render(
            request,
            "admin_dashboard.html",
            {"users": users}
        )

    return redirect("login")



class CreateAdminView(View):

    def get(self, request):
        return render(request, "create_admin.html")

    def post(self, request):
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect("create_admin")

        User.objects.create(
            username=username,
            email=email,
            password=make_password(password),
            role="ADMIN",
            created_by=request.user  
        )

        messages.success(request, "Admin created successfully")
        return redirect("adminpanel")



class UpdateAdminView(LoginRequiredMixin, View):

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != "SUPERADMIN":
            messages.error(request, "Permission denied.")
            return redirect("adminpanel")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, pk):
        admin_user = get_object_or_404(User, id=pk, role="ADMIN")
        return render(request, "update_admin.html", {
            "admin_user": admin_user
        })

    def post(self, request, pk):
        admin_user = get_object_or_404(User, id=pk, role="ADMIN")

        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")

        if User.objects.filter(username=username).exclude(id=pk).exists():
            messages.error(request, "Username already exists.")
            return redirect("update_admin", pk=pk)

        admin_user.username = username
        admin_user.email = email

        if password:
            admin_user.password = make_password(password)

        admin_user.save()

        messages.success(request, "Admin updated successfully.")
        return redirect("adminpanel") 


class DeleteAdminView(LoginRequiredMixin, View):

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != "SUPERADMIN":
            messages.error(request, "Permission denied.")
            return redirect("adminpanel")
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, pk):
        admin_user = get_object_or_404(User, id=pk, role="ADMIN")

        if admin_user == request.user:
            messages.error(request, "You cannot delete yourself.")
            return redirect("adminpanel")

        admin_user.delete()
        messages.success(request, "Admin deleted successfully.")
        return redirect("adminpanel")



class CreateUserView(LoginRequiredMixin, View):

    def dispatch(self, request, *args, **kwargs):
        if request.user.role not in ["SUPERADMIN", "ADMIN"]:
            messages.error(request, "You don't have permission to access this page.")
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        if request.user.role == "SUPERADMIN":
            admins = User.objects.filter(role="ADMIN")
        else:
            admins = None

        return render(request, "create_user.html", {
            "admins": admins
        })

    def post(self, request):
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")

        if not username or not email or not password:
            messages.error(request, "All fields are required.")
            return redirect("create_user")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("create_user")

        if request.user.role == "SUPERADMIN":
            assigned_admin_id = request.POST.get("assigned_admin")

            if not assigned_admin_id:
                messages.error(request, "Please select an admin.")
                return redirect("create_user")

            assigned_admin = get_object_or_404(
                User, id=assigned_admin_id, role="ADMIN"
            )
        else:
            assigned_admin = request.user

        
        User.objects.create(
            username=username,
            email=email,
            password=make_password(password),
            role="USER",
            assigned_admin=assigned_admin
        )

        messages.success(request, "User created successfully!")
        return redirect("adminpanel")



class UpdateUserView(LoginRequiredMixin, View):

    def dispatch(self, request, *args, **kwargs):
        if request.user.role not in ["SUPERADMIN", "ADMIN"]:
            messages.error(request, "You don't have permission.")
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, pk):

        user_obj = get_object_or_404(User, id=pk, role="USER")

        
        if request.user.role == "ADMIN" and user_obj.assigned_admin != request.user:
            messages.error(request, "Not allowed.")
            return redirect("adminpanel")

        admins = None
        if request.user.role == "SUPERADMIN":
            admins = User.objects.filter(role="ADMIN")

        return render(request, "update_user.html", {
            "user_obj": user_obj,
            "admins": admins
        })

    def post(self, request, pk):

        user_obj = get_object_or_404(User, id=pk, role="USER")

        if request.user.role == "ADMIN" and user_obj.assigned_admin != request.user:
            messages.error(request, "Not allowed.")
            return redirect("adminpanel")

        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")

        user_obj.username = username
        user_obj.email = email

        if password:
            user_obj.password = make_password(password)

        if request.user.role == "SUPERADMIN":
            assigned_admin_id = request.POST.get("assigned_admin")
            assigned_admin = get_object_or_404(User, id=assigned_admin_id, role="ADMIN")
            user_obj.assigned_admin = assigned_admin

        user_obj.save()

        messages.success(request, "User updated successfully!")
        return redirect("adminpanel")



class DeleteUserView(LoginRequiredMixin, View):

    def dispatch(self, request, *args, **kwargs):
        if request.user.role not in ["SUPERADMIN", "ADMIN"]:
            messages.error(request, "You don't have permission to access this page.")
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, pk):
        user = get_object_or_404(User, id=pk, role="USER")
        user.delete()
        messages.success(request, "User deleted successfully!")
        return redirect("adminpanel")








#Api Sections

class TaskCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    # authentication_classes=[authentication.BasicAuthentication]
    authentication_classes=[JWTAuthentication]

    def post(self, request):

        # Only ADMIN and SUPERADMIN can create task
        if request.user.role not in ["ADMIN", "SUPERADMIN"]:
            return Response(
                {"error": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = CreateTaskSerializer(
            data=request.data,
            context={"request": request}
        )

        if serializer.is_valid():
            task = serializer.save(created_by=request.user)

            return Response({
                "message": "Task created successfully",
                "task_id": task.id
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class UserTaskListView(APIView):
    permission_classes = [IsAuthenticated]
    # authentication_classes=[authentication.BasicAuthentication]

    authentication_classes=[JWTAuthentication]

    def get(self, request):
        tasks = Task.objects.filter(assigned_to=request.user)
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)
    

class TaskUpdateApiView(APIView):
    permission_classes = [IsAuthenticated]
    # authentication_classes=[authentication.BasicAuthentication]
    authentication_classes=[JWTAuthentication]

    def put(self, request, pk):

        task = get_object_or_404(Task, pk=pk, assigned_to=request.user)

        status = request.data.get("status")

        if status == "COMPLETED":
            if not request.data.get("completion_report") or not request.data.get("worked_hours"):
                return Response(
                    {"error": "Completion report and worked hours required"},
                    status=400
                )

        serializer = TaskSerializer(task, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=400)   
    

class TaskReportView(APIView):
    permission_classes = [IsAuthenticated]
    # authentication_classes=[authentication.BasicAuthentication]
    authentication_classes=[JWTAuthentication]

    def get(self, request, pk):

        if request.user.role not in ['ADMIN', 'SUPERADMIN']:
            return Response({"error": "Permission denied"}, status=403)

        task = get_object_or_404(Task, pk=pk, status="COMPLETED")

        return Response({
            "title": task.title,
            "completion_report": task.completion_report,
            "worked_hours": task.worked_hours
        })
    


class TaskUpdateView(LoginRequiredMixin, View):

    def get(self, request, pk):
        task = get_object_or_404(Task, pk=pk)

        if request.user.role not in ['ADMIN', 'SUPERADMIN']:
            return Response({"error": "Permission denied"}, status=403)

        return render(request, "task_update.html", {"task": task})

    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        if request.user.role not in ['ADMIN', 'SUPERADMIN']:
            return Response({"error": "Permission denied"}, status=403)

        status_value = request.POST.get("status")
        completion_report = request.POST.get("completion_report")
        worked_hours = request.POST.get("worked_hours")

      
        if status_value == "Completed":
            if not completion_report or not worked_hours:
                messages.error(request, "Completion report and worked hours are required.")
                return redirect("task_update", pk=pk)

            task.completion_report = completion_report
            task.worked_hours = worked_hours

        task.status = status_value
        task.save()

        messages.success(request, "Task updated successfully.")
        return redirect("adminpanel")




class TaskDeleteView(LoginRequiredMixin, View):

    def get(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        if request.user.role not in ['ADMIN', 'SUPERADMIN']:
            return Response({"error": "Permission denied"}, status=403)
        
        return redirect("adminpanel")

    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk)

        if request.user.role not in ['ADMIN', 'SUPERADMIN']:
            return Response({"error": "Permission denied"}, status=403)

        task.delete()
        messages.success(request, "Task deleted successfully.")
        return redirect("adminpanel")




def logout_view(request):
    logout(request)
    return redirect('login')