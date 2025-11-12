from django.contrib import admin
from .models import Dataset

@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = ("id", "filename", "created_at")
    search_fields = ("filename",)
    ordering = ("-created_at",)
