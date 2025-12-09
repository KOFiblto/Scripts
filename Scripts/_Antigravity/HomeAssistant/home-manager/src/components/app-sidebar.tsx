'use client'

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { LayoutDashboard, Map, Settings, Home } from "lucide-react"

const sidebarItems = [
    {
        title: "Floorplans",
        href: "/dashboard/floorplans",
        icon: Map,
    },
    {
        title: "Devices",
        href: "/dashboard/devices", // Placeholder for now
        icon: LayoutDashboard,
    },
    {
        title: "Settings",
        href: "/dashboard/settings", // Placeholder
        icon: Settings,
    },
]

export function AppSidebar() {
    const pathname = usePathname()

    return (
        <div className="w-64 border-r bg-muted/40 h-screen flex flex-col p-4">
            <div className="flex items-center gap-2 px-2 py-4 mb-4">
                <Home className="w-6 h-6" />
                <span className="font-bold text-lg">Home Manager</span>
            </div>

            <nav className="flex-1 space-y-1">
                {sidebarItems.map((item) => {
                    const isActive = pathname.startsWith(item.href)
                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={cn(
                                "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                                isActive
                                    ? "bg-primary text-primary-foreground"
                                    : "hover:bg-muted text-muted-foreground hover:text-foreground"
                            )}
                        >
                            <item.icon className="w-4 h-4" />
                            {item.title}
                        </Link>
                    )
                })}
            </nav>

            <div className="text-xs text-muted-foreground px-2 py-4">
                v0.1.0 Alpha
            </div>
        </div>
    )
}
