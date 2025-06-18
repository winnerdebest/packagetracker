from django.urls import path
from . import views


urlpatterns = [
    path('', views.track_package_view, name='track_package'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.admin_logout_view, name='logout'),
    path('track/results/', views.package_results_view, name='package_results'),
    path('packages/', views.list_packages_view, name='list_packages'),
    path('create-package/', views.create_package, name='create_package'),
    path('add-history/<int:package_id>/', views.add_delivery_history, name='add_delivery_history'),
]