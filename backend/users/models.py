from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Модель пользователя(кастом)."""
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name',)

    GUEST = 'guest'
    AUTHORIZED = 'authorized'
    ADMIN = 'admin'

    USER_ROLES = [
        (GUEST, 'guest'),
        (AUTHORIZED, 'authorized'),
        (ADMIN, 'admin'),
    ]

    username = models.CharField(
        blank=False,
        max_length=150,
        unique=True,
        verbose_name='Пользователь',
    )

    email = models.EmailField(
        max_length=254,
        unique=True,
        verbose_name='Email',
    )

    first_name = models.CharField(
        blank=False,
        max_length=150,
        verbose_name='Имя',
    )

    last_name = models.CharField(
        blank=False,
        max_length=150,
        verbose_name='Фамилия',
    )

    password = models.CharField(
        max_length=150,
        verbose_name='Пароль',
    )

    role = models.CharField(
        default='guest',
        choices=USER_ROLES,
        max_length=10,
        verbose_name='Уровень доступа пользователей',
    )

    @property
    def is_guest(self):
        """Проверка наличия прав неавторизованного пользователя (гостя)."""
        return self.role == self.GUEST

    @property
    def is_authorized(self):
        """Проверка наличия прав авторизованного пользователя."""
        return self.role == self.AUTHORIZED

    @property
    def is_admin(self):
        """Проверка наличия прав администратора."""
        return self.role == self.ADMIN or self.is_superuser

    class Meta:
        ordering = ('id',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Follow(models.Model):
    """Подписка на авторов."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор'
    )

    class Meta:
        ordering = ('user', 'author')
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'author',),
                name='unique_follow'
            ),
        )
