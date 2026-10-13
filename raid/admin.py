from django.contrib import admin
from .models import Player,Question,Attempt,Clear,RaidState

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display=('nickname','created_at','id')
    search_fields=('nickname',)

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display=('code','title','category','difficulty','concept','is_active')
    list_filter=('category','difficulty','concept','is_active')
    search_fields=('title','body','concept')

@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display=('player','question','is_correct','patch_correct','case_correct','hint_used','created_at')
    list_filter=('is_correct','question__category','question__difficulty')
    readonly_fields=('player','question','selected_line','patch_text','selected_case',
                     'patch_correct','case_correct','hint_used','is_correct','created_at')

@admin.register(Clear)
class ClearAdmin(admin.ModelAdmin):
    list_display=('player','question','damage','created_at')
    readonly_fields=('player','question','damage','created_at')

@admin.register(RaidState)
class RaidStateAdmin(admin.ModelAdmin):
    list_display=('remaining_hp','max_hp','damage_per_clear')
