ONGOING:
[-] default runner = cli or gui

SET1
[] print should by default push to ui and as well print in cli, flag print2ui = True
[] button "Clear & Re-run" change label to "Clear" and it should only clear result (without reexecution)
[] BUG: when long or async commands are executed, Run Command button should be disabled and greyed out
[] prepare seperate file per ui_block
[] fix python release script - when there is error with release (e.g. pypi) store it as unreleased, ask to release on next execution
--
SET2
1.[] by default long should be set to true, change "long" attribute to "threaded"
2.[] ui should provide access to flet page using ui.hold.page, ui.hold.result['command name] - flet control responsible for output, this will allow customizations, show sample customization in example 04
3.[] there should be decorator @ui.init() for method that will be called initially when gui is started, add it to example 04 with method that will present flet dialog
using native flet control
--
SET3
prepare additional ui block Alert(title:str, content:ui_block) that will present flet AlertDialog (in gui mode). Alert will be triggered like so
tu.Link("Alert", on_click=lambda: ui(tu.Alert("Please note!",tu.Md("## content"))))
alert will have only "ok" button that will close alert
prepare additional component Confirm("Confirm","Are you sure that you want to run?",on_yes=callable,on_no=callable)
in cli mode it will simply present content and ask for confirm
put example to 03_ui_blocks that will popup dialog on Link click

--
[] add proper python typing
[] add support for sub-applications app = typer.Typer() app.add_typer(users_app, name="users") app.add_typer(orders_app, name="orders") app.add_typer(reports_app, name="reports").

[] extract AppShell?

REVIEW
[-] change bootstrap convention to app and upp

TODO

[] logger UI
[] popup result
[] multi module app
[] argument based exceptions
[] density

prepare proposition of console(CLIRunnerCtx) and get_JSON() methods in UIBlock
refactor modules

DONE
[x] BUG when there is threaded execution of command error is not presented immediately, it is presented only after successfull execution of command (error + correct execution)

# UIBlock interface clarification together with UIRunner

---

UIBlockType = str | Callable[[],Any] | UIBlock

UIBlock
def build(ctx:UIRunnerCtx) -> ft.Control
...

UIRunnerCtx
def instance() # static method to get current runner ctx (required for ui)

def ui_flow_append(UIBlockType):
...

def build_child(parent:UIBlock,child:UIBlockType):
if isinstance(child,str): # this is markdown
markdown = child
return tu.Md(markdown)
if callable(child): # prepare list view to retrieve ui flow
lv = ListView()
self.ui_flow_stack.append(lv)
result = child() # if result is of UIBlockType, then build it as well
self.ui_flow_stack.pop()
#if lv has only single element return it
#otherwise return list

# EXAMPLE

class UITab:
label:str
content:UIBlockType

UITabs:
tabs:list[UITab]
def build(ctx:UIRunnerCtx) -> ft.Control
ft_tabs = ft.Tabs()
for t in self.tabs:
flet_tab = ft.Tab(text=t.label,content=ctx.build_child(self,t.content))
ft.tabs.tabs.append(flet_tab)
return ft_tabs
