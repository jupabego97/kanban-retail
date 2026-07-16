"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Boxes } from "lucide-react";
import { useAuth } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function LoginPage() {
  const { login, user, loading } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("admin@tienda.local");
  const [password, setPassword] = useState("Admin123!");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!loading && user) router.replace("/demandas");
  }, [loading, user, router]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      await login(email, password);
      toast.success("Bienvenido");
      router.replace("/demandas");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Credenciales inválidas");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="from-background via-background to-muted flex min-h-screen items-center justify-center bg-gradient-to-br p-4">
      <Card className="w-full max-w-md border-border/60 shadow-2xl">
        <CardHeader className="space-y-3 text-center">
          <div className="bg-primary text-primary-foreground mx-auto flex size-12 items-center justify-center rounded-xl">
            <Boxes className="size-6" />
          </div>
          <CardTitle className="text-2xl">Kanban Retail</CardTitle>
          <CardDescription>
            Capture la demanda que hoy se pierde en mostrador y conviértala en decisiones de
            surtido.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={(e) => void onSubmit(e)}>
            <div className="space-y-2">
              <Label htmlFor="email">Correo</Label>
              <Input
                id="email"
                type="email"
                autoComplete="username"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Contraseña</Label>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            <Button className="w-full" type="submit" disabled={busy}>
              {busy ? "Ingresando…" : "Ingresar"}
            </Button>
            <p className="text-muted-foreground text-center text-xs">
              Demo: admin@tienda.local / Admin123!
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
