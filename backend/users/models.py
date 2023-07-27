from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
from django.db import models

from users.validator import validate_username

MAX_LENGTH = 150


class User(AbstractUser):
    """Модель пользователя"""
    email = models.EmailField(
        'Электронная почта',
        max_length=256,
        unique=True,
        blank=False,
        null=False,
    )
    username = models.CharField(
        'Имя пользователя',
        max_length=MAX_LENGTH,
        unique=True,
        blank=False,
        null=False,
        validators=[validate_username, ]
    )
    first_name = models.CharField(
        'Имя',
        max_length=MAX_LENGTH,
        blank=False,
        null=False,
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=MAX_LENGTH,
        blank=False,
        null=False,
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'username']

    class Meta:
        ordering = ('last_name', 'first_name',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Follow(models.Model):
    """Модель подписки"""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='followers',
        verbose_name='Автор'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_follow'
            )
        ]
        ordering = ('id',)

    def __str__(self):
        return f'{self.user} подписался на {self.author}'

    def clean(self):
        if self.user == self.author:
            raise ValidationError('Ой, на себя подписываться нельзя!')

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
