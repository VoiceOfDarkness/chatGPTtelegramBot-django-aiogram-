from django.db import models
from django.utils import timezone


class User(models.Model):
    username = models.CharField(max_length=50)
    user_text = models.TextField()
    bot_text = models.TextField()
    created = models.DateField(default=timezone.now)

    def __str__(self) -> str:
        return f'user {self.username}'
