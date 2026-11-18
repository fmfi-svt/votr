"""Griffe extension used by the API docs (loaded from zensical.toml)."""

import re
from typing import override

import griffe

_internal_re = re.compile(r"(^|\n)\s*Internal\b")


def _is_internal(obj: griffe.Object | griffe.Alias) -> bool:
    """An object is considered internal if its name looks private (`_foo` but
    not `__foo__`), or if its docstring contains a paragraph starting with the
    word "Internal".
    """
    if isinstance(obj, griffe.Alias):
        # Don't look at `Alias.docstring`. Resolving the `Alias`'s final target
        # causes some kind of infinite loop.
        return False
    if obj.docstring and _internal_re.search(obj.docstring.value):
        return True
    if obj.name.startswith("__") and obj.name.endswith("__"):
        return False
    return obj.name.startswith("_")


class VotrExtension(griffe.Extension):
    """Shows private members, and labels internal ones with "internal"."""

    @override
    def on_object(
        self,
        *,
        obj: griffe.Object,
        loader: griffe.GriffeLoader,
        **kwargs: object,
    ) -> None:
        # Label internal objects.
        if _is_internal(obj):
            obj.labels.add("internal")

        # Show almost everything, including internal objects, because these docs
        # are both for Votr API users and Votr developers (insert Venn diagram
        # joke here).
        #
        # But skip objects which are internal AND undocumented AND (private
        # global variables OR component `_ais_*` setters). There really isn't
        # anything interesting about them, and they waste too much space.
        #
        # Zensical uses this thanks to `filters = "public"` in zensical.toml.
        obj.public = not (
            "internal" in obj.labels
            and obj.docstring is None
            and (
                "module-attribute" in obj.labels or obj.name.startswith("_ais_")
            )
        )

        # Use almost source order, but public < internal.
        members = list(obj.members.items())
        members.sort(key=lambda t: _is_internal(t[1]))
        obj.members = dict(members)
