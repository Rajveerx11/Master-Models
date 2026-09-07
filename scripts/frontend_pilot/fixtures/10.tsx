import React from 'react';
import {AiStatusBarControls} from '@/modules/ai/components/AiStatusBarControls';
import {useChatStore} from '@/modules/ai/store/chatStore';
import {MODELS,providerNeedsKey} from '@/modules/ai/config';
const cloud=MODELS.find(m=>providerNeedsKey(m.provider))!;
const local=MODELS.find(m=>!providerNeedsKey(m.provider))!;
useChatStore.setState({apiKeys:{},selectedModelId:cloud.id});
Object.assign(window,{pilot:{store:useChatStore,local,cloud,settingsCalls:[]}});
export default function Fixture(){return <AiStatusBarControls/>;}
