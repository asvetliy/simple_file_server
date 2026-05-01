from django.apps import apps
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractBaseUser
from django.db import models
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.contrib.auth.models import PermissionsMixin, UserManager
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


def get_default_storage_quote():
    StorageQuote = apps.get_model('files', 'StorageQuote')
    return StorageQuote.objects.filter(is_default=True).order_by('quota_bytes', 'name').first()


class CustomUserManager(UserManager):
    use_in_migrations = True

    def _create_user(self, username, password, **extra_fields):
        """
        Create and save a user with the given username, email, and password.
        """
        if not username:
            raise ValueError('The given username must be set')
        # Lookup the real model class from the global app registry so this
        # manager method can be used in migrations. This is fine because
        # managers are by definition working on the real model.
        GlobalUserModel = apps.get_model(self.model._meta.app_label, self.model._meta.object_name)
        username = GlobalUserModel.normalize_username(username)
        extra_fields.setdefault('storage_quote', get_default_storage_quote())
        user = self.model(username=username, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(username, password, **extra_fields)

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(username, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    username_validator = UnicodeUsernameValidator()

    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        validators=[username_validator],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    storage_quote = models.ForeignKey(
        'files.StorageQuote',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='users',
    )

    objects = CustomUserManager()

    @property
    def storage_quota_bytes(self):
        if self.storage_quote_id:
            return self.storage_quote.quota_bytes
        return settings.DEFAULT_STORAGE_QUOTA_BYTES

    @property
    def storage_used_bytes(self):
        File = apps.get_model('files', 'File')
        return sum(file.file.size for file in File.objects.filter(user=self) if file.file)

    @property
    def storage_remaining_bytes(self):
        return max(self.storage_quota_bytes - self.storage_used_bytes, 0)

    @property
    def storage_usage_percent(self):
        quota = self.storage_quota_bytes
        if quota <= 0:
            return 100
        return min(round((self.storage_used_bytes / quota) * 100), 100)

    def save(self, *args, **kwargs):
        if self.storage_quote_id is None:
            self.storage_quote = get_default_storage_quote()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        # abstract = True
        db_table = 'users'
