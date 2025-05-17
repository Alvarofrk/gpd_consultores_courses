from django import template
from datetime import timedelta

register = template.Library()


@register.inclusion_tag("quiz/correct_answer.html", takes_context=True)
def correct_answer_for_all(context, question):
    """
    processes the correct answer based on a given question object
    if the answer is incorrect, informs the user
    """
    answers = question.get_choices()
    incorrect_list = context.get("incorrect_questions", [])
    if question.id in incorrect_list:
        user_was_incorrect = True
    else:
        user_was_incorrect = False

    return {"previous": {"answers": answers}, "user_was_incorrect": user_was_incorrect}


@register.filter
def multiply(value, arg):
    """Multiplica el valor por el argumento"""
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        return ''


@register.filter
def add_days(value, days):
    """Añade días a una fecha"""
    try:
        return value + timedelta(days=int(days))
    except (ValueError, TypeError):
        return value


@register.filter
def answer_choice_to_string(question, answer_id):
    return question.answer_choice_to_string(answer_id)
