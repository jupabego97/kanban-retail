import { CaptureForm } from "@/components/demand/capture-form";

export default function CapturaPage() {
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Captura rápida</h1>
        <p className="text-muted-foreground text-sm">
          Diseñada para mostrador: menos de 15 segundos por solicitud.
        </p>
      </div>
      <CaptureForm />
    </div>
  );
}
