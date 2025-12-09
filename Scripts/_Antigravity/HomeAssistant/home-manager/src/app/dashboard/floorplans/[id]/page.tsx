import { prisma } from "@/lib/prisma"
import { notFound } from "next/navigation"
import { FloorplanViewer } from "@/components/floorplan-viewer"
import { DeviceForm } from "@/components/device-form"
import { Dialog, DialogContent, DialogTrigger, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Plus } from "lucide-react"

export default async function FloorplanDetailPage({ params }: { params: { id: string } }) {
    const { id } = await params

    const floorplan = await prisma.floorplan.findUnique({
        where: { id },
        include: { devices: true }
    })

    if (!floorplan) {
        notFound()
    }

    return (
        <div className="h-screen flex flex-col">
            <div className="p-4 border-b flex justify-between items-center bg-background z-10">
                <h1 className="text-xl font-bold">{floorplan.name}</h1>
                <div className="flex gap-2">
                    <Dialog>
                        <DialogTrigger asChild>
                            <Button>
                                <Plus className="w-4 h-4 mr-2" />
                                Add Device
                            </Button>
                        </DialogTrigger>
                        <DialogContent>
                            <DialogTitle>Add Device</DialogTitle>
                            <DeviceForm floorplanId={floorplan.id} />
                        </DialogContent>
                    </Dialog>
                </div>
            </div>
            <div className="flex-1 overflow-hidden bg-slate-100 dark:bg-slate-900 relative">
                <FloorplanViewer floorplan={floorplan} devices={floorplan.devices} />
            </div>
        </div>
    )
}
