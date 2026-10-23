from django.conf import settings


def demonstration_status(request):
    return {'academic_demo': settings.ACADEMIC_DEMO}
