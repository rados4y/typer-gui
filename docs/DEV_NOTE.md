ONGOING:
[] introduce app_shell.py, bugfix all issues

[-] BUG: when long or async commands are executed, Run Command button should be disabled and greyed out

[] add systray functionality, add param to UiAPP(systray:bool=False), follow concept from https://github.com/ndonkoHenri/Flet-as-System-Tray-Icon. Closure should minimize to systray. On systray right click there should be "close" button and "Open". When i click systray app should be opened. Minimize should simply minimize app.
[] add proper python typing

[] extract AppShell?

REVIEW
[-] change bootstrap convention to app and upp
[-] default runner = cli or gui
[-] print should by default push to ui and as well print in cli, flag print2ui = True 1.[-] by default long should be set to true, change "long" attribute to "threaded"
[-] ui should provide access to flet page using ui.hold.page, ui.hold.result['command name] - flet control responsible for output, this will allow customizations, show sample customization in example 04

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
