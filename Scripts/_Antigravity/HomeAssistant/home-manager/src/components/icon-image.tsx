'use client'

import Image from "next/image"
import { useState } from "react"
import { Box } from "lucide-react"

export function IconImage({ type, value }: { type: 'device' | 'protocol', value: string }) {
    const folder = type === 'device' ? 'devices' : 'protocols'
    const src = `/assets/icons/${folder}/${value.toLowerCase()}.png`
    const [error, setError] = useState(false)

    if (error) {
        // Fallback icon
        return <Box className="w-8 h-8 text-muted-foreground p-1" />
    }

    return (
        <div className="relative w-8 h-8">
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
