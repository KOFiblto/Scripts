'use client'

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Plus } from "lucide-react"
import { createFloorplan } from "@/actions/floorplans"

export function AddFloorplanButton() {
    const [open, setOpen] = useState(false)
    const [loading, setLoading] = useState(false)

    async function handleSubmit(formData: FormData) {
        setLoading(true)
        // We need to read image dimensions here to pass them to server option or server action reads them.
        // In step 4 implementation, I made server action read width/height from formData.
        // So we must handle file selection, load it to get dimensions, then append to formData?
        // Or just let server action handle it if we used a library?
        // Current server action expects 'width' and 'height' in formData.
        // So we should intercept submission.

        // Actually, form action={createFloorplan} processes it directly.
        // But we need to inject width/height.
        // So we'll use onSubmit handler.

        const file = formData.get('file') as File
        if (file) {
            const img = new Image()
            img.src = URL.createObjectURL(file)
            await new Promise((resolve) => {
                img.onload = () => {
                    formData.set('width', img.width.toString())
                    formData.set('height', img.height.toString())
                    resolve(true)
                }
            })
        }

        await createFloorplan(formData)
        setLoading(false)
        setOpen(false)
    }

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
                <Card className="flex flex-col items-center justify-center p-6 border-dashed cursor-pointer hover:bg-muted/50 transition-colors h-full min-h-[300px]">
                    <div className="p-4 rounded-full bg-muted mb-4">
                        <Plus className="w-8 h-8 text-muted-foreground" />
                    </div>
                    <h3 className="font-semibold text-lg mb-1">Add Floorplan</h3>
                    <p className="text-sm text-muted-foreground text-center">Upload a new floorplan image</p>
                </Card>
            </DialogTrigger>
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>Add New Floorplan</DialogTitle>
                    <DialogDescription>Upload an image of your floorplan. It will be saved locally.</DialogDescription>
                </DialogHeader>
                <form action={handleSubmit} className="space-y-4">
                    <div className="space-y-2">
                        <Label htmlFor="name">Name</Label>
                        <Input id="name" name="name" placeholder="Ground Floor" required />
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="file">Floorplan Image</Label>
                        <Input id="file" name="file" type="file" accept="image/*" required />
                    </div>
                    <DialogFooter>
                        <Button type="submit" disabled={loading}>
                            {loading ? 'Uploading...' : 'Create Floorplan'}
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    )
}
