from django.contrib import admin
from django.db.models import Count, Sum
from django.urls import reverse
from django.utils.html import format_html

from .models import Player, Question, Attempt, Clear, RaidState


class ReadOnlyHistoryInline(admin.TabularInline):
    """Player's existing history is visible, but cannot be altered here."""
    extra = 0
    can_delete = False
    show_change_link = False

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class ClearInline(ReadOnlyHistoryInline):
    model = Clear
    verbose_name = "해결한 문제"
    verbose_name_plural = "해결한 문제 · 보스 공격 기록"
    fields = ("question", "damage", "created_at")
    readonly_fields = fields
    ordering = ("-created_at", "-id")


class AttemptInline(ReadOnlyHistoryInline):
    model = Attempt
    verbose_name = "문제 제출"
    verbose_name_plural = "제출 이력 · 오답 포함"
    fields = ("question", "selected_line", "choice_number", "is_correct", "hint_used", "created_at")
    readonly_fields = fields
    ordering = ("-created_at", "-id")

    @admin.display(description="선택한 보기")
    def choice_number(self, obj):
        return f"{obj.selected_choice + 1}번" if obj.selected_choice is not None else "-"


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    # Keep the separate Players list, and show both histories on each player's detail page.
    list_display = ("nickname", "solved_count", "submitted_count", "created_at")
    list_display_links = ("nickname",)
    search_fields = ("nickname",)
    list_per_page = 50
    readonly_fields = ("id", "created_at", "solved_missions", "damage_contribution")
    fields = ("nickname", "id", "created_at", "solved_missions", "damage_contribution")
    inlines = (ClearInline, AttemptInline)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _solved_count=Count("clears", distinct=True),
            _submitted_count=Count("attempts", distinct=True),
        )

    @admin.display(description="해결 문제", ordering="_solved_count")
    def solved_count(self, obj):
        return obj._solved_count

    @admin.display(description="제출 횟수", ordering="_submitted_count")
    def submitted_count(self, obj):
        return obj._submitted_count

    @admin.display(description="해결한 미션")
    def solved_missions(self, obj):
        clears = obj.clears.select_related("question").order_by("question__code")
        return ", ".join(f"{clear.question.code} ({clear.question.title})" for clear in clears) or "아직 해결한 미션이 없습니다."

    @admin.display(description="총 공격 기여")
    def damage_contribution(self, obj):
        return f"{obj.clears.aggregate(total=Sum('damage'))['total'] or 0} HP"


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "category", "difficulty", "concept", "is_active")
    list_filter = ("category", "difficulty", "concept", "is_active")
    search_fields = ("code", "title", "body", "concept")


class HunterLinkMixin:
    @admin.display(description="헌터")
    def hunter_link(self, obj):
        url = reverse("admin:raid_player_change", args=[obj.player_id])
        return format_html('<a href="{}">{}</a>', url, obj.player.nickname)


@admin.register(Attempt)
class AttemptAdmin(HunterLinkMixin, admin.ModelAdmin):
    # Separate global submissions list, searchable/filterable by hunter.
    list_display = ("hunter_link", "question", "selected_line", "choice_number", "is_correct", "hint_used", "created_at")
    list_display_links = ("question",)
    list_filter = ("is_correct", "question__category", "question__difficulty", "player")
    search_fields = ("player__nickname", "question__code", "question__title")
    list_select_related = ("player", "question")
    ordering = ("-created_at", "-id")
    readonly_fields = ("player", "question", "selected_line", "patch_text", "selected_case",
                       "selected_choice", "patch_correct", "case_correct", "hint_used",
                       "is_correct", "created_at")

    @admin.display(description="선택한 보기")
    def choice_number(self, obj):
        return f"{obj.selected_choice + 1}번" if obj.selected_choice is not None else "-"


@admin.register(Clear)
class ClearAdmin(HunterLinkMixin, admin.ModelAdmin):
    # Separate global solved-questions list, with direct links to individual hunters.
    list_display = ("hunter_link", "question", "damage", "created_at")
    list_display_links = ("question",)
    list_filter = ("question__category", "question__difficulty", "player")
    search_fields = ("player__nickname", "question__code", "question__title")
    list_select_related = ("player", "question")
    ordering = ("-created_at", "-id")
    readonly_fields = ("player", "question", "damage", "created_at")


@admin.register(RaidState)
class RaidStateAdmin(admin.ModelAdmin):
    list_display = ("remaining_hp", "max_hp", "damage_per_clear")
