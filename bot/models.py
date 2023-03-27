from django.db import models


class User(models.Model):
    username = models.CharField(max_length=50)
    user_text = models.TextField()
    user_voice = models.FileField(upload_to='voices/', null=True, blank=True)
    bot_text = models.TextField()
    created = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f'user {self.username}'
