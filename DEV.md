Introduce UIApp and UICommand classes that will provide context, common operations and allow easy operations and extensions. UIApp should be available from UI class.
Following methods/attributes should be exposed:
UIApp:

- cmd - reference to current UICommand that is selected or being executed
- commands - list of UICommand
- blocks.header - reference to header flet control that allows to add additional flet components (part of possible customizations)
- blocks.body - reference to application body flet control

UICommand:

- select - operation that allows to select command
- run - run operation
- include - include execution of operation into current operation
- output - current outcome of executed command
- blocks.arguments - flet section with arguments
- blocks.title - flet section with title
- blocks.actions - flet section with "Run command"
- blocks.result - flet section with result of command

=====
task 1.
NO BACKWARD compatibilty, clean up old code
UIApp should have attribute out that will have list of available ui blocks, it can be used e.g.:
ui.out.table()
ui.out.md() # markdown

move all ui block components from UIApp to UIApp.out
fix examples

task 2. ✅ DONE
NO BACKWARD compatibilty, clean up old code
remove is_markdown @ui.command(is_markdown=True), markdown will be supported only by ui.out.md()

task 3 ✅ DONE
NO BACKWARD compatibilty, clean up old code
ui.link and ui.button should have do methods like so
ui.out.link("Refresh data",do=lambda:ui.runtime.get_command("refresh").select())

task 4
NO BACKWARD compatibilty, clean up old code
current code
--
@app.command()
@ui.command(is_button=True) # Display as prominent button
def greet():
...
--
should be refactored, i can provide attribute block that will return ui.block component which will be used to present command
so it should be right now supported as:
--
@app.command()
@ui.command(block=lambda:ui.out.button("Greet",do:lambda:ui.call("greet")))
def greet():
...
--
or simpler, ui component will be called with UICommand as command attribute
@app.command()
@ui.command(block=ui.out.button)
def greet():
...
--
