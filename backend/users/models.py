from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """Модель пользователя"""
    email = models.EmailField(
        'Электронная почта',
        max_length=64,
        unique=True,
        blank=False,
        null=False,
    )
    username = models.CharField(
        'Имя пользователя',
        max_length=20,
        unique=True,
        blank=False,
        null=False,
    )
    first_name = models.CharField(
        'Имя',
        max_length=20,
        blank=False,
        null=False,
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=20,
        blank=False,
        null=False,
    )
    password = models.CharField(
        'Пароль',
        max_length=20,
        blank=False,
        null=False,
    )

    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='Groups',
        blank=True,
        related_name='user_set_custom',
    )

    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='User permissions',
        blank=True,
        related_name='user_set_custom', 
    )

    class Meta:
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

    def __str__(self):
        return f'{self.user} подписался на {self.author}'

    def clean(self):
        if self.user == self.author:
            raise ValidationError('Ой, на себя подписываться нельзя!')
