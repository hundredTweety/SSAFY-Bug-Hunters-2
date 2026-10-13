# Initial schema, created for BUG HUNTERS 2.0 (fresh database required).
import uuid
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(name='Player',fields=[
            ('id',models.UUIDField(primary_key=True,serialize=False,editable=False,default=uuid.uuid4)),
            ('nickname',models.CharField(max_length=16)),
            ('created_at',models.DateTimeField(auto_now_add=True)),
        ]),
        migrations.CreateModel(name='Question',fields=[
            ('id',models.BigAutoField(primary_key=True,serialize=False,auto_created=True,verbose_name='ID')),
            ('code',models.CharField(max_length=24,unique=True)),
            ('category',models.CharField(max_length=16,choices=[('array','배열·문자열'),('grid','2차원·시뮬레이션'),('search','탐색·자료구조'),('strategy','그리디·DP')])),
            ('concept',models.CharField(max_length=50)),
            ('difficulty',models.PositiveSmallIntegerField(default=1)),
            ('title',models.CharField(max_length=120)),
            ('body',models.TextField()),
            ('buggy_code',models.TextField()),
            ('original_line',models.TextField()),
            ('accepted_patches',models.JSONField()),
            ('case_options',models.JSONField()),
            ('counterexample_index',models.PositiveSmallIntegerField()),
            ('hint',models.TextField()),
            ('explanation',models.TextField()),
            ('is_active',models.BooleanField(default=True)),
        ],options={'ordering':['category','code']}),
        migrations.CreateModel(name='RaidState',fields=[
            ('id',models.PositiveSmallIntegerField(primary_key=True,default=1,editable=False,serialize=False)),
            ('max_hp',models.PositiveIntegerField(default=1000)),
            ('remaining_hp',models.PositiveIntegerField(default=1000)),
            ('damage_per_clear',models.PositiveIntegerField(default=20)),
        ]),
        migrations.CreateModel(name='Attempt',fields=[
            ('id',models.BigAutoField(primary_key=True,serialize=False,auto_created=True,verbose_name='ID')),
            ('selected_line',models.PositiveIntegerField(default=0)),
            ('patch_text',models.CharField(max_length=300,blank=True)),
            ('selected_case',models.PositiveSmallIntegerField(null=True,blank=True)),
            ('patch_correct',models.BooleanField(default=False)),
            ('case_correct',models.BooleanField(default=False)),
            ('hint_used',models.BooleanField(default=False)),
            ('is_correct',models.BooleanField()),
            ('created_at',models.DateTimeField(auto_now_add=True)),
            ('player',models.ForeignKey(to='raid.player',related_name='attempts',on_delete=django.db.models.deletion.CASCADE)),
            ('question',models.ForeignKey(to='raid.question',related_name='attempts',on_delete=django.db.models.deletion.CASCADE)),
        ],options={'ordering':['id']}),
        migrations.CreateModel(name='Clear',fields=[
            ('id',models.BigAutoField(primary_key=True,serialize=False,auto_created=True,verbose_name='ID')),
            ('damage',models.PositiveIntegerField(default=0)),
            ('created_at',models.DateTimeField(auto_now_add=True)),
            ('player',models.ForeignKey(to='raid.player',related_name='clears',on_delete=django.db.models.deletion.CASCADE)),
            ('question',models.ForeignKey(to='raid.question',related_name='clears',on_delete=django.db.models.deletion.CASCADE)),
        ],options={'ordering':['created_at']}),
        migrations.AddIndex(model_name='attempt',index=models.Index(fields=['player','question','id'],name='hunt_attempt_pq_idx')),
        migrations.AddConstraint(model_name='clear',constraint=models.UniqueConstraint(fields=['player','question'],name='hunt_unique_clear')),
    ]
