import React from 'react';
import {Tooltip,TooltipProvider,TooltipTrigger,TooltipContent} from '@/components/ui/tooltip';
export default function Fixture(){
  return <TooltipProvider><main style={{display:'grid',gridTemplateColumns:'repeat(2, 240px)',gap:70,paddingTop:50,marginLeft:200}}>
  {(['top','bottom','left','right'] as const).flatMap(side=>['default','custom'].map(variant=><Tooltip key={side+variant}>
    <TooltipTrigger asChild><button data-testid={side+'-'+variant}>{side} {variant}</button></TooltipTrigger>
    <TooltipContent side={side} className={variant==='custom'?'bg-red-600 text-white':undefined}>Surface {side} {variant}</TooltipContent>
  </Tooltip>))}</main></TooltipProvider>;
}
