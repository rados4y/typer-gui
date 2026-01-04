TODO:
def_command(view=True, auto_scroll=True)
prepare proposition of console(CLIRunnerCtx) and get_JSON() methods in UIBlock
refactor modules

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
