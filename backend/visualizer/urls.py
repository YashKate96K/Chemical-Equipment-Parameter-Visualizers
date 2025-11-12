from django.urls import path
from .views import upload_csv, list_datasets, dataset_report, dataset_health

urlpatterns = [
    path('upload/', upload_csv, name='upload'),
    path('datasets/', list_datasets, name='datasets'),
    path('datasets/<int:pk>/report/', dataset_report, name='dataset_report'),
    path('datasets/<int:pk>/health/', dataset_health, name='dataset_health'),
]
