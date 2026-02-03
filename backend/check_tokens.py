#!/usr/bin/env python
import os
import sys
import django

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

print("=== Users and Tokens ===")
users = User.objects.all()
if not users.exists():
    print("No users found. Creating test user...")
    user = User.objects.create_user(username='testuser', password='testpass123')
    token = Token.objects.create(user=user)
    print(f"Created user: {user.username} with token: {token.key}")
else:
    for user in users:
        token = Token.objects.filter(user=user).first()
        if token:
            print(f"User: {user.username} - Token: {token.key}")
        else:
            token = Token.objects.create(user=user)
            print(f"User: {user.username} - Created new token: {token.key}")

print("\n=== Valid Tokens for Frontend ===")
for user in users:
    token = Token.objects.filter(user=user).first()
    if token:
        print(f"Token: {token.key} (User: {user.username})")
