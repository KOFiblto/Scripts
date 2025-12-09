'use client'

import Image from "next/image"
import { useState } from "react"
import { Box } from "lucide-react"

import { cn } from "@/lib/utils"

export function IconImage({ type, value, className }: { type: 'device' | 'protocol', value: string, className?: string }) {
    const folder = type === 'device' ? 'devices' : 'protocols'
    const src = `/assets/icons/${folder}/${value.toLowerCase()}.png`
    const [error, setError] = useState(false)

    if (error) {
        // Fallback icon
        return <Box className={cn("w-8 h-8 text-muted-foreground p-1", className)} />
    }

    return (
        <div className={cn("relative w-8 h-8", className)}>
            <Image
                src={src}
                alt={value}
                fill
                className="object-contain"
                onError={() => setError(true)}
            />
        </div>
    )
}
