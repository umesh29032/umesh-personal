from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_alter_user_user_type'),
        ('inventory', '0010_seed_roles_and_stage_codes'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='extra_roles',
            field=models.ManyToManyField(
                blank=True,
                help_text='Additional access grants. Stack on top of the primary role.',
                related_name='extra_users',
                to='inventory.role',
                verbose_name='Extra Roles',
            ),
        ),
    ]
