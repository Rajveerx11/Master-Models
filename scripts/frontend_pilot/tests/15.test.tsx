import { describe, expect, it } from 'vitest';
import { setLeafCwd, type PaneNode } from '@/modules/terminal/lib/panes';

function fixture(): PaneNode {
  return {kind:'split',id:1,dir:'row',children:[
    {kind:'split',id:2,dir:'col',children:[{kind:'leaf',id:3,cwd:'/old'},{kind:'leaf',id:4,cwd:'/sibling'}]},
    {kind:'leaf',id:5,cwd:'/other'},
  ]};
}
describe('pane cwd structural sharing', () => {
  it('preserves root identity for an unknown leaf', () => {
    const root=fixture(); expect(setLeafCwd(root,999,'/new')).toBe(root);
  });
  it('preserves root identity when the cwd is unchanged', () => {
    const root=fixture(); expect(setLeafCwd(root,3,'/old')).toBe(root);
  });
  it('changes only the target leaf and ancestors, without mutating input', () => {
    const root=fixture(); const before=structuredClone(root); const next=setLeafCwd(root,3,'/new');
    expect(root).toEqual(before); expect(next).not.toBe(root);
    if(root.kind!=='split'||next.kind!=='split') throw new Error('fixture must be split');
    expect(next.children[1]).toBe(root.children[1]);
    const oldBranch=root.children[0], newBranch=next.children[0];
    if(oldBranch.kind!=='split'||newBranch.kind!=='split') throw new Error('nested split required');
    expect(newBranch).not.toBe(oldBranch);
    expect(newBranch.children[1]).toBe(oldBranch.children[1]);
    expect(newBranch.children[0]).toEqual({kind:'leaf',id:3,cwd:'/new'});
  });
});
