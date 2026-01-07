import { useMemo } from "react"
import { alignParagraphs, computeSmartDiff } from "@/lib/diff-utils"
import { cn } from "@/lib/utils"

interface DiffViewProps {
    original: string
    rewritten: string
}

export function DiffView({ original, rewritten }: DiffViewProps) {
    const alignPairs = useMemo(() => alignParagraphs(original, rewritten), [original, rewritten])

    return (
        <div className="flex flex-col gap-4">
            <div className="flex gap-4 font-bold pb-2 border-b">
                <div className="flex-1">Original</div>
                <div className="flex-1">Rewritten</div>
            </div>
            {alignPairs.map((pair, idx) => (
                <div key={idx} className="flex gap-4 items-start min-h-[3em] py-2 border-b border-dashed border-gray-100 last:border-0 hover:bg-slate-50">
                    <div className="flex-1 text-sm leading-relaxed text-muted-foreground whitespace-pre-wrap">
                        {pair.original || <span className="text-gray-200 select-none">-</span>}
                    </div>
                    <div className="flex-1 text-sm leading-relaxed whitespace-pre-wrap">
                        {pair.rewritten ? (
                            <DiffParagraph original={pair.original} rewritten={pair.rewritten} />
                        ) : (
                            <span className="text-gray-200 select-none">-</span>
                        )}
                    </div>
                </div>
            ))}
        </div>
    )
}

function DiffParagraph({ original, rewritten }: { original: string; rewritten: string }) {
    const parts = useMemo(() => computeSmartDiff(original, rewritten), [original, rewritten])

    return (
        <>
            {parts.map((part, i) => (
                <span
                    key={i}
                    className={cn(
                        part.type === 'insert' && "bg-green-100 text-green-800 decoration-green-300 underline decoration-2 underline-offset-2",
                        part.type === 'delete' && "bg-red-50 text-red-300 line-through decoration-red-200 hidden", /* We usually hide deletions in the 'rewritten' text or show them? */
                        part.type === 'equal' && "text-foreground"
                    )}
                    title={part.type !== 'equal' ? part.type : undefined}
                >
                    {part.text}
                </span>
            ))}
        </>
    )
}
