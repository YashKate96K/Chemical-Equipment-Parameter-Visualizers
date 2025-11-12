from rest_framework import serializers
from .models import Dataset

class DatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dataset
        fields = ['id', 'filename', 'created_at', 'summary_json']

class UploadResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    filename = serializers.CharField()
    summary_json = serializers.JSONField()
    preview_csv = serializers.CharField()
