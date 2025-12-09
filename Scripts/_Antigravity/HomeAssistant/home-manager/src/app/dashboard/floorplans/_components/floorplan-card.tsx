import Image from "next/image"
import { Floorplan } from "@prisma/client"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import Link from "next/link"
import { Edit } from "lucide-react"

interface FloorplanCardProps {
    floorplan: Floorplan
}

export function FloorplanCard({ floorplan }: FloorplanCardProps) {
    return (
        <Link href={`/dashboard/floorplans/${floorplan.id}`} className="block transition-transform hover:scale-[1.02]">
            <Card className="overflow-hidden h-full">
                <div className="aspect-video relative bg-muted">
                    <Image
                        src={floorplan.imagePath}
                        alt={floorplan.name}
                        fill
                        className="object-cover"
                    />
                </div>
                <CardHeader>
                    <CardTitle>{floorplan.name}</CardTitle>
                </CardHeader>
                <CardFooter className="flex justify-between">
                    <div className="text-sm text-muted-foreground">
                        {floorplan.width} x {floorplan.height} px
                    </div>
                    <Button variant="ghost" size="sm" className="pointer-events-none">
                        <Edit className="w-4 h-4 mr-2" />
                        Edit
                    </Button>
                </CardFooter>
            </Card>
        </Link>
    )
}
