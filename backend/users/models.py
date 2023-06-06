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
        verbose_name='Username',
    )

    email = models.EmailField(
        max_length=254,
        unique=True,
        verbose_name='Email',
    )

    first_name = models.CharField(
        blank=False,
        max_length=150,
        verbose_name='First Name',
    )

    last_name = models.CharField(
        blank=False,
        max_length=150,
        verbose_name='Last Name',
    )

    password = models.CharField(
        max_length=150,
        verbose_name='Password',
    )

    role = models.CharField(
        default='guest',
        choices=USER_ROLES,
        max_length=10,
        verbose_name='User Role',
    )

    @property
    def is_guest(self):
        """Checking for unauthorized user rights (guest)."""
        return self.role == self.GUEST

    @property
    def is_authorized(self):
        """Checking for authorized user rights."""
        return self.role == self.AUTHORIZED

    @property
    def is_admin(self):
        """Checking for administrator rights."""
        return self.role == self.ADMIN or self.is_superuser

    class Meta:
        ordering = ('id',)
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.username


class Follow(models.Model):
    """
    Подписка на авторов.
    Пользователь (user) и автор рецепта (author) связаны с моделью User.
    """
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
