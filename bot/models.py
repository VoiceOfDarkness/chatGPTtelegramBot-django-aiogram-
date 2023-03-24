from django.db import models


class User(models.Model):
    username = models.CharField(max_length=50)
    user_text = models.TextField()
    bot_text = models.TextField()
    created = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f'user {self.username}'
