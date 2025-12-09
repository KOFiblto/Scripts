import { prisma } from "@/lib/prisma"
import { AddFloorplanButton } from "./_components/add-floorplan-button"
import { FloorplanCard } from "./_components/floorplan-card"

export default async function FloorplansPage() {
    const floorplans = await prisma.floorplan.findMany({
        orderBy: { createdAt: 'desc' }
    })

    return (
        <div className="p-8 space-y-8">
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">Floorplans</h2>
                    <p className="text-muted-foreground">Manage your home layouts and devices.</p>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {floorplans.map((fp) => (
                    <FloorplanCard key={fp.id} floorplan={fp} />
                ))}
                <AddFloorplanButton />
            </div>
        </div>
    )
}
