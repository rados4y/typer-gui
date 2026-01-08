ONGOING:
[-] change package to typer2ui
[-] change bootstrap convention to app and upp
[] add list as checkboxes
[] if there are prints -> currently each of them produces single ft.Text(), i prefer to verify if it was lastly presented add simply new line to previous one.
[] fix release - when there is error with release, retry with same version (right now version is increased)
[] button "Clear & Re-run" change to clear
[] add proper python typing
[] not working def depl(version:str, natco:str, envs:list[str]):
[] add support for sub-applications app = typer.Typer() app.add_typer(users_app, name="users") app.add_typer(orders_app, name="orders") app.add_typer(reports_app, name="reports").

[] prepare seperate file per ui_block
[] extract AppShell?

TODO

[] logger UI
[] popup result
[] multi module app
[] argument based exceptions
[] density

prepare proposition of console(CLIRunnerCtx) and get_JSON() methods in UIBlock
refactor modules

DONE

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
