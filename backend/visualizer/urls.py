from django.urls import path
from .views import upload_csv, list_datasets, dataset_report, dataset_health, register_user, dataset_rows

urlpatterns = [
    path('upload/', upload_csv, name='upload_csv'),
    path('datasets/', list_datasets, name='list_datasets'),
    path('datasets/<int:pk>/rows/', dataset_rows, name='dataset_rows'),
    path('datasets/<int:pk>/health/', dataset_health, name='dataset_health'),
    path('datasets/<int:pk>/report/', dataset_report, name='dataset_report'),
    path('auth/register/', register_user, name='register_user'),
]
