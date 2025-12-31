"""Data source interface for dynamic data loading."""

from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Any


class DataSource(ABC):
    """Abstract interface for dynamic data loading with pagination, sorting, and filtering.

    Implementations should provide data fetching logic that supports:
    - Pagination: offset/limit parameters
    - Sorting: sort_by column name and ascending direction
    - Filtering: filter_text for full-text search

    Example:
        class UserDataSource(DataSource):
            def __init__(self, database):
                self.db = database

            def fetch(self, offset, limit, sort_by=None, ascending=True, filter_text=None):
                query = self.db.query(User)

                # Apply filter
                if filter_text:
                    query = query.filter(User.name.contains(filter_text))

                # Apply sorting
                if sort_by:
                    column = getattr(User, sort_by)
                    query = query.order_by(column if ascending else column.desc())

                # Get total count before pagination
                total = query.count()

                # Apply pagination
                results = query.offset(offset).limit(limit).all()
                rows = [[u.name, u.email, u.role] for u in results]

                return rows, total
    """

    @abstractmethod
    def fetch(
        self,
        offset: int,
        limit: int,
        sort_by: Optional[str] = None,
        ascending: bool = True,
        filter_text: Optional[str] = None,
    ) -> Tuple[List[List[Any]], int]:
        """Fetch a page of data with optional sorting and filtering.

        Args:
            offset: Number of rows to skip (for pagination)
            limit: Maximum number of rows to return
            sort_by: Column name to sort by (None for no sorting)
            ascending: Sort direction (True for ascending, False for descending)
            filter_text: Text to filter/search for (None for no filtering)

        Returns:
            Tuple of (rows, total_count) where:
            - rows: List of row data for the current page (each row is a list of cell values)
            - total_count: Total number of rows matching the filter (for pagination info)

        Example:
            # Fetch page 2 (rows 10-19), sorted by name ascending, filtered by "john"
            rows, total = source.fetch(offset=10, limit=10, sort_by="name",
                                      ascending=True, filter_text="john")
            # Returns: (10 rows, 47 total matching records)
        """
        pass
