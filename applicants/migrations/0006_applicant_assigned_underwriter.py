import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('applicants', '0005_applicant_account'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='applicant', name='assigned_underwriter',
            field=models.ForeignKey(
                to=settings.AUTH_USER_MODEL, null=True, blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='assigned_applications',
                limit_choices_to={'profile__role': 'UNDERWRITER', 'is_active': True,
                                  'is_staff': False, 'is_superuser': False},
            ),
        ),
    ]
