from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Модель юзера с ролями (в условии написано,
    что одни пользователи создают опросы, а другие их проходят)"""

    class Role(models.TextChoices):
        AUTHOR = "AUTHOR", "Автор опросов"
        RESPONDENT = "RESPONDENT", "Респондент"
        ADMIN = "ADMIN", "Администратор"

    role = models.CharField(
        max_length=20, choices=Role.choices, default=Role.RESPONDENT
    )


class Poll(models.Model):
    """Модель опроса"""

    title = models.CharField(
        max_length=255,
        verbose_name="Название",
        help_text="Введите название опроса",
    )
    author = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="polls",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активен",
    )

    def __str__(self):
        return self.title


class Question(models.Model):
    """Модель вопроса"""

    poll = models.ForeignKey(
        "Poll",
        on_delete=models.CASCADE,
        related_name="questions",
    )
    text = models.TextField(
        verbose_name="Текст вопроса",
        help_text="Введите текст вопроса",
    )
    order = models.IntegerField(
        default=0,
        verbose_name="Порядок",
        help_text="Введите приоритет, по умолчанию равен '0'",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активен",
    )

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(
                fields=["poll", "order"],
                condition=models.Q(is_active=True),
                name="unique_active_question_order",
            )
        ]

    def __str__(self):
        return self.text[:50]


class Choice(models.Model):
    """Модель варианта ответа на вопрос"""

    question = models.ForeignKey(
        "Question",
        on_delete=models.CASCADE,
        related_name="choices",
    )
    text = models.CharField(
        max_length=255,
        verbose_name="Вариант ответа",
        help_text="Введите вариант ответа",
    )
    order = models.IntegerField(
        default=0,
        verbose_name="Порядок",
        help_text="Введите приоритет, по умолчанию равен '0'",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-order"]
        constraints = [
            models.UniqueConstraint(
                fields=["question", "order"],
                condition=models.Q(is_active=True),
                name="unique_active_choice_order",
            )
        ]

    def __str__(self):
        return self.text[:50]


class PollSession(models.Model):
    """Модель сессии определенного юзера с определенным опросом"""

    user = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="sessions",
    )
    poll = models.ForeignKey(
        "Poll",
        on_delete=models.CASCADE,
        related_name="sessions",
    )
    started_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Время начала опроса",
    )
    finished_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Время окончания опроса",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "poll"], name="unique_user_poll"),
            models.Index(
                fields=["finished_at"],
                name="idx_finished_at",
                condition=models.Q(finished_at__isnull=False),
            ),
        ]


class UsersAnswer(models.Model):
    """Модель ответов юзеров"""

    session = models.ForeignKey(
        PollSession,
        on_delete=models.CASCADE,
        related_name="answers",
        db_index=False,
    )
    question = models.ForeignKey(
        "Question",
        on_delete=models.PROTECT,
    )
    choice = models.ForeignKey(
        "Choice",
        on_delete=models.PROTECT,
        db_index=False,
    )

    class Meta:

        constraints = [
            models.UniqueConstraint(
                fields=["session", "question"], name="unique_session_question"
            )
        ]
