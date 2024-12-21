from django.contrib import admin
from .models import Comment

def delete_duplicates(modeladmin, request, queryset):
    duplicates = (
        Comment.objects.values('student', 'session', 'term')
        .annotate(count=models.Count('id'))
        .filter(count__gt=1)
    )

    for duplicate in duplicates:
        student = duplicate['student']
        session = duplicate['session']
        term = duplicate['term']

        comments = Comment.objects.filter(student=student, session=session, term=term)
        latest_comment = comments.latest('created_at')
        comments.exclude(id=latest_comment.id).delete()

delete_duplicates.short_description = "Delete duplicate comments"

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('student', 'session', 'term', 'author', 'created_at')
    actions = [delete_duplicates]
