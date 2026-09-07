"""Apply the scoped pilot fixes through the real, append-only edit tool."""
from scripts.run_frontend_pilot import OUT, write_json, tool

def edit(number, path, pairs):
    call=OUT/'edit-call.json'
    write_json(call, dict(name='edit', arguments=dict(path=path, edits=[dict(oldText=a,newText=b) for a,b in pairs])))
    tool(number,call)

if __name__ == '__main__':
    edit(1,'apps/desktop/src/components/ui/input.tsx',[(
        'focus-visible:ring-ring flex h-9','focus-visible:ring-primary/40 focus-visible:border-primary flex h-8'),(
        'text-sm shadow-sm transition-colors','text-xs transition-colors'),(
        'focus-visible:ring-1 disabled:','focus-visible:ring-2 disabled:')])
    edit(15,'src/modules/terminal/lib/panes.ts',[(
        '  if (isLeaf(n)) return n.id === id ? { ...n, cwd } : n;\n  return { ...n, children: n.children.map((c) => setLeafCwd(c, id, cwd)) };',
        '  if (isLeaf(n)) return n.id === id && n.cwd !== cwd ? { ...n, cwd } : n;\n  const children = n.children.map((c) => setLeafCwd(c, id, cwd));\n  return children.every((c, i) => c === n.children[i]) ? n : { ...n, children };')])
    edit(29,'src/modules/tabs/lib/useTabs.ts',[(
        'export type TerminalTab = {','export const MAX_PANES_PER_TAB = 8;\n\nexport type TerminalTab = {'),(
        '          const splitId = nextIdRef.current++;',
        '          if (leafIds(t.paneTree).length >= MAX_PANES_PER_TAB) return t;\n          const splitId = nextIdRef.current++;')])
    edit(10,'src/modules/ai/store/chatStore.ts',[(
        '  DEFAULT_MODEL_ID,\n  getModel,','  DEFAULT_MODEL_ID,\n  getModel,\n  providerNeedsKey,'),(
        '  return !!apiKeys[getModel(modelId).provider];',
        '  const provider = getModel(modelId).provider;\n  return !providerNeedsKey(provider) || !!apiKeys[provider];'),(
        '  if (!getActiveProviderKey()) return false;',
        '  if (!hasKeyForModel(state.selectedModelId)) return false;')])
