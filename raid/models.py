import uuid
from django.db import models

class Player(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nickname = models.CharField(max_length=16)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.nickname

class Question(models.Model):
    CATEGORY_CHOICES = [
        ('array','배열·문자열'),('grid','2차원·시뮬레이션'),
        ('search','탐색·자료구조'),('strategy','그리디·DP'),
    ]
    code = models.CharField(max_length=24, unique=True)
    category = models.CharField(max_length=16, choices=CATEGORY_CHOICES)
    concept = models.CharField(max_length=50)
    difficulty = models.PositiveSmallIntegerField(default=1)
    title = models.CharField(max_length=120)
    body = models.TextField()
    buggy_code = models.TextField()
    original_line = models.TextField()
    accepted_patches = models.JSONField()
    choices = models.JSONField(default=list)  # Exactly four authored patches; one correct
    case_options = models.JSONField()
    counterexample_index = models.PositiveSmallIntegerField()
    hint = models.TextField()
    explanation = models.TextField()
    is_active = models.BooleanField(default=True)
    class Meta:
        ordering = ['category','code']
    def __str__(self):
        return f'{self.code} · {self.title}'

class RaidState(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True,default=1,editable=False)
    max_hp = models.PositiveIntegerField(default=1000)
    remaining_hp = models.PositiveIntegerField(default=1000)
    damage_per_clear = models.PositiveIntegerField(default=20)
    def __str__(self):
        return f'보스 HP {self.remaining_hp}/{self.max_hp}'

class Attempt(models.Model):
    player = models.ForeignKey(Player,on_delete=models.CASCADE,related_name='attempts')
    question = models.ForeignKey(Question,on_delete=models.CASCADE,related_name='attempts')
    selected_line = models.PositiveIntegerField(default=0)
    patch_text = models.CharField(max_length=300,blank=True)
    selected_case = models.PositiveSmallIntegerField(null=True,blank=True)
    selected_choice = models.PositiveSmallIntegerField(null=True,blank=True)
    patch_correct = models.BooleanField(default=False)
    case_correct = models.BooleanField(default=False)
    hint_used = models.BooleanField(default=False)
    is_correct = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['id']
        indexes = [models.Index(fields=['player','question','id'],name='hunt_attempt_pq_idx')]

class Clear(models.Model):
    player = models.ForeignKey(Player,on_delete=models.CASCADE,related_name='clears')
    question = models.ForeignKey(Question,on_delete=models.CASCADE,related_name='clears')
    damage = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['created_at']
        constraints = [models.UniqueConstraint(fields=['player','question'],name='hunt_unique_clear')]
