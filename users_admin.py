# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos Ventures SL

from django.apps import apps

from django.contrib import admin
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from .models import Role, User
from .forms import UserChangeForm, UserCreationForm


SEPARATOR = "<strong>&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;</strong>"

admin.site.unregister(Group)


## Inlines

class RoleInline(admin.TabularInline):
    model = Role
    extra = 0


## Admin panels

class RoleAdmin(admin.ModelAdmin):
    list_display = ["name"]
    filter_horizontal = ("permissions",)

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if db_field.name == "permissions":
            qs = kwargs.get("queryset", db_field.rel.to.objects)
            # Avoid a major performance hit resolving permission names which
            # triggers a content_type load:
            kwargs["queryset"] = qs.select_related("content_type")
        return super().formfield_for_manytomany(
            db_field, request=request, **kwargs)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "email", "full_name")
    list_filter = ("is_superuser", "is_active", "verified_email")
    search_fields = ("username", "full_name", "email")
    ordering = ("username",)
    readonly_fields = (
        "total_private_projects", "total_memberships_private_projects",
        "total_public_projects", "total_memberships_public_projects",
    )
    filter_horizontal = ()
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("PERSONAL INFO"), {"fields": ("full_name", "email", "bio", "photo")}),
        (_("EXTRA INFO"), {"fields": ("color", "lang", "timezone", "token", "colorize_tags",
                                      "email_token", "new_email", "verified_email", "accepted_terms", "read_new_terms")}),
        (_("PERMISSIONS"), {"fields": ("is_active", "is_superuser")}),
        (_("IMPORTANT DATES"), {"fields": (("last_login", "date_joined", "date_cancelled"),)}),
        # (_("PROJECT OWNERSHIPS RESTRICTIONS"), {"fields": (("max_private_projects", "max_memberships_private_projects"),
        #                                 ("max_public_projects", "max_memberships_public_projects"))}),
        (_("PROJECT OWNERSHIPS STATS"), {"fields": (("total_private_projects",
                                                     "total_memberships_private_projects"),
                                                    ("total_public_projects",
                                                     "total_memberships_public_projects"))}),
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2')}
        ),
    )
    form = UserChangeForm
    add_form = UserCreationForm

    @admin.display(
        description=_("Private projects owned")
    )
    def total_private_projects(self, obj):
        return obj.owned_projects.filter(is_private=True).count()

    @admin.display(
        description=_("Private memberships owned")
    )
    def total_memberships_private_projects(self, obj):
        Membership = apps.get_model("projects", "Membership")
        accepted = (Membership.objects.filter(project__is_private=True,
                                          project__owner_id=obj.id,
                                          user_id__isnull=False)
                                  .order_by("user_id")
                                  .distinct("user_id").count())
        pending = (Membership.objects.filter(project__is_private=True,
                                          project__owner_id=obj.id,
                                          user_id__isnull=True)
                                  .order_by("email")
                                  .distinct("email").count())
        total = pending + accepted
        return mark_safe(f"{total}{SEPARATOR}<i>{accepted} accepted</i>{SEPARATOR}<i>{pending} pending</i>")

    @admin.display(
        description=_("Public projects owned")
    )
    def total_public_projects(self, obj):
        return obj.owned_projects.filter(is_private=False).count()

    @admin.display(
        description=_("Public memberships owned")
    )
    def total_memberships_public_projects(self, obj):
        Membership = apps.get_model("projects", "Membership")
        accepted =  (Membership.objects.filter(project__is_private=False,
                                          project__owner_id=obj.id,
                                          user_id__isnull=False)
                                  .order_by("user_id")
                                  .distinct("user_id").count())
        pending = (Membership.objects.filter(project__is_private=False,
                                          project__owner_id=obj.id,
                                          user_id__isnull=True)
                                  .order_by("email")
                                  .distinct("email").count())
        total = pending + accepted
        return mark_safe(f"{total}{SEPARATOR}<i>{accepted} accepted</i>{SEPARATOR}<i>{pending} pending</i>")


