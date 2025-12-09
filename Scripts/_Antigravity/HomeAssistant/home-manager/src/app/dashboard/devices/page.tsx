import { prisma } from "@/lib/prisma"
import { DevicesTable } from "@/components/devices-table"

export default async function DevicesPage() {
    const devices = await prisma.device.findMany({
        include: { floorplan: true },
        orderBy: { createdAt: 'desc' }
    })

    return (
        <DevicesTable devices={devices} />
    )
}
