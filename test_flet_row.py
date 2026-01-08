"""Test Flet Row layout to verify horizontal checkbox arrangement."""
import flet as ft

def main(page: ft.Page):
    page.title = "Flet Row Test"
    page.window.width = 600
    page.window.height = 400

    # Test 1: Checkboxes in a Row
    checkboxes_row = ft.Row(
        controls=[
            ft.Checkbox(label="Low"),
            ft.Checkbox(label="Medium", value=True),
            ft.Checkbox(label="High"),
            ft.Checkbox(label="Urgent"),
        ],
        spacing=10,
        wrap=True,
    )

    # Test 2: Same structure as our code
    test_control = ft.Column(
        controls=[
            ft.Text("priority *", weight=ft.FontWeight.BOLD),
            ft.Row(
                controls=[
                    ft.Checkbox(label="low"),
                    ft.Checkbox(label="medium", value=True),
                    ft.Checkbox(label="high"),
                    ft.Checkbox(label="urgent"),
                ],
                spacing=10,
                wrap=True,
            ),
        ],
        spacing=5,
    )

    page.add(
        ft.Text("Test 1: Checkboxes in Row", size=16, weight=ft.FontWeight.BOLD),
        checkboxes_row,
        ft.Divider(),
        ft.Text("Test 2: Column with label + Row (our structure)", size=16, weight=ft.FontWeight.BOLD),
        test_control,
    )

if __name__ == "__main__":
    ft.app(target=main)
