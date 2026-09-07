import { afterEach, describe, expect, it } from 'vitest';
import { act, createElement } from 'react';
import { createRoot } from 'react-dom/client';
import { useTabs, type TerminalTab } from '@/modules/tabs/lib/useTabs';
import { leafIds } from '@/modules/terminal/lib/panes';
let cleanup=()=>{};
afterEach(()=>cleanup());
describe('per-tab pane limit', () => {
  it('caps at eight, preserves blocked state, permits other tabs and reopening capacity', () => {
    globalThis.IS_REACT_ACT_ENVIRONMENT=true;
    const result:{current:ReturnType<typeof useTabs>}= {current:null as unknown as ReturnType<typeof useTabs>};
    function Probe(){ result.current=useTabs(); return null; }
    const container=document.createElement('div'); document.body.append(container);
    const renderer=createRoot(container);
    act(()=>renderer.render(createElement(Probe)));
    cleanup=()=>{act(()=>renderer.unmount());container.remove();};
    const tab=(id=1):TerminalTab=>{
      const found=result.current.tabs.find(t=>t.id===id);
      if(!found||found.kind!=='terminal') throw new Error('missing terminal');
      return found;
    };
    for(let i=0;i<6;i++) act(()=>{result.current.splitActivePane(1,'row');});
    expect(leafIds(tab().paneTree)).toHaveLength(7);
    act(()=>{result.current.splitActivePane(1,'col');});
    expect(leafIds(tab().paneTree)).toHaveLength(8);
    const before=tab();
    act(()=>{result.current.splitActivePane(1,'row');});
    expect(leafIds(tab().paneTree)).toHaveLength(8);
    expect(tab().paneTree).toBe(before.paneTree); expect(tab().activeLeafId).toBe(before.activeLeafId);
    let second=0;
    act(()=>{second=result.current.newTab('/second');});
    act(()=>{result.current.splitActivePane(second,'row');});
    expect(leafIds(tab(second).paneTree)).toHaveLength(2);
    act(()=>{result.current.closePaneByLeaf(tab().activeLeafId);});
    expect(leafIds(tab().paneTree)).toHaveLength(7);
    act(()=>{result.current.splitActivePane(1,'col');});
    expect(leafIds(tab().paneTree)).toHaveLength(8);
  });
});
