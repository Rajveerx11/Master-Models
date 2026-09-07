import { beforeEach, describe, expect, it, vi } from 'vitest';
const calls=vi.hoisted(()=>({send:vi.fn(async()=>{})}));
vi.mock('@ai-sdk/react',()=>({Chat:class { sendMessage=calls.send; }}));
vi.mock('@/modules/ai/lib/transport',()=>({createContextAwareTransport:()=>({})}));
import { hasKeyForModel, sendMessage, useChatStore } from '@/modules/ai/store/chatStore';
import { MODELS, providerNeedsKey } from '@/modules/ai/config';
const local=MODELS.find(m=>!providerNeedsKey(m.provider));
const cloud=MODELS.find(m=>providerNeedsKey(m.provider));
if(!local||!cloud) throw new Error('fixture needs both provider kinds');
beforeEach(()=>{
  calls.send.mockClear();
  const keys=Object.fromEntries(Object.keys(useChatStore.getState().apiKeys).map(k=>[k,null]));
  useChatStore.setState({apiKeys:keys,activeSessionId:'fixture-session',selectedModelId:local.id});
});
describe('keyless provider contract',()=>{
  it('accepts keyless models but rejects missing cloud credentials',()=>{
    expect(hasKeyForModel(local.id)).toBe(true); expect(hasKeyForModel(cloud.id)).toBe(false);
  });
  it('sends through the recording SDK boundary once',async()=>{
    expect(await sendMessage('fixture message')).toBe(true);
    expect(calls.send).toHaveBeenCalledExactlyOnceWith({text:'fixture message'});
  });
  it('blocks missing session and missing required key, allows supplied key',async()=>{
    useChatStore.setState({activeSessionId:null});
    expect(await sendMessage('blocked')).toBe(false);
    useChatStore.setState({activeSessionId:'cloud-fixture',selectedModelId:cloud.id});
    expect(await sendMessage('blocked')).toBe(false); expect(calls.send).not.toHaveBeenCalled();
    useChatStore.getState().setApiKey(cloud.provider,'dummy-test-key');
    expect(await sendMessage('permitted')).toBe(true); expect(calls.send).toHaveBeenCalledTimes(1);
  });
});
