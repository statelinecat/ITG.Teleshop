from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('flower_shop', '0015_alter_user_email'),  # Замените на имя предыдущей миграции
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='username',
            field=models.CharField(max_length=150, unique=False, verbose_name='Имя пользователя'),
        ),
    ]