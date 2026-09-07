import React,{useState} from 'react';
import {Input} from '@/components/ui/input';
export default function Fixture(){
  const [value,setValue]=useState('');
  return <main><div style={{display:'flex',gap:16,alignItems:'center'}}>
    <Input aria-label="Project name" value={value} onChange={e=>setValue(e.target.value)}/>
    <button style={{height:32,minWidth:80}} onClick={()=>setValue('reset')}>Reset</button>
  </div><output data-testid="value">{value}</output><Input aria-label="Disabled" disabled value="locked" readOnly/>
  <div data-testid="primary" style={{background:'var(--primary)',width:20,height:20}}/></main>;
}
