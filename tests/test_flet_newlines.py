"""Simple Flet test for text with newlines"""

import flet as ft


def main(page: ft.Page):
    page.title = "Flet Newlines Test"
    page.padding = 20

    # Test 1: Text with \n newline characters
    text_with_newlines = "Line 1\nLine 2\nLine 3\nLine 4"

    page.add(
        ft.Text(
            "Test 1: String with \\n characters",
            weight=ft.FontWeight.BOLD,
            selectable=True,
        ),
        ft.Text(text_with_newlines, selectable=True),
        ft.Divider(),
        ft.Text("Test 2: Multi-line string with newlines", weight=ft.FontWeight.BOLD),
        ft.Text("First line\nSecond line\nThird line"),
        ft.Divider(),
        ft.Text("Test 3: Triple-quoted string", weight=ft.FontWeight.BOLD),
        ft.Text(
            """Line A
Line B
Line C"""
        ),
        ft.Divider(),
        ft.Text("Test 4: Mixed content", weight=ft.FontWeight.BOLD),
        ft.Text("Header\n\nBody text here\n\nFooter"),
    )


if __name__ == "__main__":
    ft.app(target=main)
