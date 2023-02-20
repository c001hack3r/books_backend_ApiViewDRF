from django.contrib import admin
from store.models import Book, UserBookRelation
from django.contrib.admin import ModelAdmin


@admin.register(Book)
class BookAdmin(ModelAdmin):
    pass

@admin.register(UserBookRelation)
class UserBookRelationAdmin(ModelAdmin):
    pass