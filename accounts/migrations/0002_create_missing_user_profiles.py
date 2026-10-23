from django.conf import settings
from django.db import migrations


def create_missing_profiles(apps, schema_editor):
    User = apps.get_model(settings.AUTH_USER_MODEL.split('.')[0], settings.AUTH_USER_MODEL.split('.')[1])
    UserProfile = apps.get_model('accounts', 'UserProfile')
    for user in User.objects.all():
        if UserProfile.objects.filter(user_id=user.pk).exists():
            continue
        role = 'ADMINISTRATOR' if user.is_staff or user.is_superuser else 'UNDERWRITER'
        UserProfile.objects.create(user_id=user.pk, role=role)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_missing_profiles, migrations.RunPython.noop),
    ]
