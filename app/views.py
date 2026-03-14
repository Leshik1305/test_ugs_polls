from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from .models import PollSession, Poll, Question, UsersAnswer, User


def get_session(user, poll):
    """Функция поиска / создания активной сессии"""
    session = PollSession.objects.filter(user=user, poll=poll).first()

    if session:
        if session.finished_at is not None:
            return session, False
        return session, True

    session = PollSession.objects.create(user=user, poll=poll)
    return session, True


def get_unanswered_question(poll, session):
    """Функция поиска неотвеченного вопроса"""
    answered_ids = UsersAnswer.objects.filter(session=session).values_list(
        "question_id", flat=True
    )
    return (
        Question.objects.filter(poll=poll, is_active=True)
        .exclude(id__in=answered_ids)
        .prefetch_related("choices")
        .first()
    )


@login_required
def get_next_question(request, poll_id):
    """Функция, которая возвращает вопрос, на который
    должен ответить пользователь в рамках опроса с id = NNN"""

    if request.user.role != User.Role.RESPONDENT:
        return JsonResponse(
            {"status": "error", "message": "Только респонденты могут проходить опросы"},
            status=403,
        )

    poll = get_object_or_404(Poll, id=poll_id, is_active=True)

    session, is_available = get_session(request.user, poll)

    if not is_available:
        return JsonResponse(
            {
                "status": "error",
                "message": "Вы уже проходили этот опрос. Повторное прохождение запрещено.",
            },
            status=400,
        )

    next_question = get_unanswered_question(poll, session)

    if not next_question:
        session.finished_at = timezone.now()
        session.save()
        return JsonResponse(
            {
                "status": "finished",
                "message": "Опрос успешно пройден",
                "poll_title": poll.title,
            }
        )

    choices_data = [
        {"id": choice.id, "text": choice.text}
        for choice in next_question.choices.filter(is_active=True)
    ]

    return JsonResponse(
        {
            "status": "success",
            "data": {
                "session_id": session.id,
                "poll_title": poll.title,
                "question": {
                    "id": next_question.id,
                    "text": next_question.text,
                    "choices": choices_data,
                },
            },
        }
    )
