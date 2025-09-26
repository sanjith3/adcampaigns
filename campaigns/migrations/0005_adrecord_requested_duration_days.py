from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('campaigns', '0004_adrecord_updated_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='adrecord',
            name='requested_duration_days',
            field=models.PositiveIntegerField(null=True, blank=True),
        ),
    ]


