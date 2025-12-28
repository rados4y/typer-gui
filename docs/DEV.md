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
clean up code organization and introduce correct code design enforcing separation of concerns, e.g.:

- single instance of Typer UI that represent root application context, it holds definition of all commands, it is central commander, knows how to handle all operations triggered by dedicated UIs (yet there is no dependency on specific UI)
- seperate class that holds complete build of flet UI, this class can be potentially replaced with other without impact on other classes
- seperate executors for UI and CLI with context
- seperate base class for Block UIs with
