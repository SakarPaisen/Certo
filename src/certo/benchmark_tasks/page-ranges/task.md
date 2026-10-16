# Page ranges

Write a Python module, using only the standard library, for the "pages to
print" box of a print dialog.

## `pages.py`

### `parse_pages(spec, last_page)`

Returns the sorted list of page numbers (no duplicates) selected by
`spec`, in a document whose pages are numbered `1` to `last_page`.

- `spec` is a comma-separated list of parts. Spaces around parts and
  around the `-` are allowed.
- A part is one of:
  - `N`: page N;
  - `A-B`: pages A to B, **both included** (A must not be greater than B);
  - `A-`: pages A to `last_page`;
  - `-B`: pages 1 to B.
- Parts may overlap: `"1-5,3-7"` is pages 1 to 7.
- Raise `ValueError` for: an empty spec, an empty part (`"1,,3"`), a part
  that isn't one of the forms above (`"a"`, `"-"`, `"1-2-3"`), a page
  below 1 or above `last_page`, `A` greater than `B`, or a `last_page`
  below 1.

### `format_pages(pages)`

The opposite direction: takes page numbers (in any order, maybe with
duplicates) and returns the shortest spec: runs of two or more
consecutive pages become `A-B`, single pages stay `N`, parts are joined
with `,` and no spaces, in increasing order. An empty list gives `""`.

Example: `[9, 1, 2, 3, 5, 8, 7, 3]` → `"1-3,5,7-9"`.

Also write pytest tests for it in `test_pages.py`.
