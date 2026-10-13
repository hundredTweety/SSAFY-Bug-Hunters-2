from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('raid','0001_initial')]
    operations = [
        migrations.AddField(model_name='question',name='choices',field=models.JSONField(default=list)),
        migrations.AddField(model_name='attempt',name='selected_choice',field=models.PositiveSmallIntegerField(blank=True,null=True)),
    ]
