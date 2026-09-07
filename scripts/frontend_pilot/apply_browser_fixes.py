"""Scoped browser fixes after captured parent baselines."""
from scripts.frontend_pilot.apply_initial_fixes import edit

if __name__=='__main__':
    edit(10,'src/modules/ai/components/AiStatusBarControls.tsx',[(
        '  PROVIDERS,\n  type ModelId,','  PROVIDERS,\n  providerNeedsKey,\n  type ModelId,'),(
        '  const currentProviderHasKey = !!apiKeys[current.provider];',
        '  const currentProviderHasKey = !providerNeedsKey(current.provider) || !!apiKeys[current.provider];'),(
        '    if (!apiKeys[providerId]) {','    if (providerNeedsKey(providerId) && !apiKeys[providerId]) {'),(
        '          const hasKey = !!apiKeys[p.id];','          const hasKey = !providerNeedsKey(p.id) || !!apiKeys[p.id];')])
    edit(20,'src/components/ui/tooltip.tsx',[(
        '          className\n',
        '          "[&>span:has(>[data-slot=tooltip-arrow])]:bg-inherit [&>span:has(>[data-slot=tooltip-arrow])]:[clip-path:polygon(0_0,100%_0,50%_100%)]",\n          className\n'),(
        '        <TooltipPrimitive.Arrow className="z-50 size-2.5 translate-y-[calc(-50%_-_2px)] rotate-45 rounded-[2px] bg-foreground fill-foreground data-[side=left]:translate-x-[-1.5px] data-[side=right]:translate-x-[1.5px]" />',
        '        {/* Radix positions/rotates a wrapper. Inherit the surface through it,\n            then clip its background to the native arrow triangle. */}\n        <TooltipPrimitive.Arrow data-slot="tooltip-arrow" className="bg-inherit fill-transparent" />')])
