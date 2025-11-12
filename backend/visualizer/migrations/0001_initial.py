from django.db import migrations, models
import django.utils.timezone

class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Dataset',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('filename', models.CharField(max_length=255)),
                ('file', models.FileField(upload_to='datasets/')),
                ('summary_json', models.JSONField()),
                ('preview_csv', models.TextField()),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]
