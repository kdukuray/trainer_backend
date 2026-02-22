"""
Cursor-based pagination for all list endpoints.

Uses the ``id`` field as the cursor, returning ``next_cursor`` in the
response so the frontend can request the next page with ``?cursor=<id>``.
"""

from rest_framework.pagination import BasePagination
from rest_framework.response import Response


class CursorPagination(BasePagination):
    """
    Simple id-based cursor pagination.

    Query params:
        cursor: The id of the last item from the previous page.
        page_size: Optional override (capped at 50).

    Response shape:
        {
            "results": [...],
            "next_cursor": "<id of last item>" | null,
            "has_more": true | false
        }
    """

    default_page_size = 20
    max_page_size = 50

    def paginate_queryset(self, queryset, request, view=None):
        """
        Slice the queryset starting after the given cursor id.

        Parameters:
            queryset: A Django QuerySet ordered by ``-id`` (or whichever pk).
            request: DRF Request containing optional ``cursor`` and ``page_size``.
            view: The API view (unused).

        Returns:
            A list of model instances for the current page.
        """
        self.request = request
        page_size = self._get_page_size(request)
        cursor = request.query_params.get("cursor")

        if cursor:
            queryset = queryset.filter(id__lt=cursor)

        items = list(queryset[:page_size + 1])

        # If we got more than page_size, there are more pages
        self.has_more = len(items) > page_size
        items = items[:page_size]

        self.next_cursor = str(items[-1].id) if items and self.has_more else None
        return items

    def get_paginated_response(self, data):
        """
        Wrap serialized data with pagination metadata.

        Parameters:
            data: The serialized list of items.

        Returns:
            DRF Response with ``results``, ``next_cursor``, and ``has_more``.
        """
        return Response(
            {
                "results": data,
                "next_cursor": self.next_cursor,
                "has_more": self.has_more,
            }
        )

    def _get_page_size(self, request) -> int:
        """Parse page_size from query params, capped at max_page_size."""
        try:
            size = int(request.query_params.get("page_size", self.default_page_size))
            return min(size, self.max_page_size)
        except (ValueError, TypeError):
            return self.default_page_size
