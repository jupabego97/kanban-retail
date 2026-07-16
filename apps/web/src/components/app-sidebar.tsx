"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  Boxes,
  ClipboardList,
  LayoutDashboard,
  LogOut,
  Package,
  Truck,
  Upload,
  Users,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";

const NAV = [
  { href: "/demandas", label: "Tablero", icon: LayoutDashboard },
  { href: "/demandas/captura", label: "Captura rápida", icon: ClipboardList },
  { href: "/catalogo", label: "Catálogo", icon: Package },
  { href: "/proveedores", label: "Proveedores", icon: Truck },
  { href: "/importar", label: "Importar CSV", icon: Upload },
  { href: "/metricas", label: "Métricas", icon: BarChart3 },
  { href: "/usuarios", label: "Usuarios", icon: Users, roles: ["OWNER", "MANAGER"] as const },
];

export function AppSidebar() {
  const pathname = usePathname();
  const { user, logout, hasRole } = useAuth();

  return (
    <aside className="bg-sidebar text-sidebar-foreground flex h-screen w-64 shrink-0 flex-col border-r border-sidebar-border">
      <div className="flex items-center gap-2 px-4 py-5">
        <div className="bg-primary text-primary-foreground flex size-9 items-center justify-center rounded-lg">
          <Boxes className="size-5" />
        </div>
        <div>
          <p className="text-sm font-semibold tracking-tight">Kanban Retail</p>
          <p className="text-muted-foreground text-xs">Demanda no atendida</p>
        </div>
      </div>
      <Separator />
      <nav className="flex flex-1 flex-col gap-1 p-3">
        {NAV.filter((item) => !item.roles || hasRole(...item.roles)).map((item) => {
          const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors",
                active
                  ? "bg-sidebar-accent text-sidebar-accent-foreground font-medium"
                  : "text-muted-foreground hover:bg-sidebar-accent/60 hover:text-foreground",
              )}
            >
              <Icon className="size-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="border-t border-sidebar-border p-3">
        <div className="mb-2 flex items-center gap-2 px-1">
          <Avatar className="size-8">
            <AvatarFallback>
              {user?.name?.slice(0, 2).toUpperCase() ?? "??"}
            </AvatarFallback>
          </Avatar>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium">{user?.name}</p>
            <p className="text-muted-foreground truncate text-xs">{user?.role}</p>
          </div>
        </div>
        <Button
          variant="ghost"
          size="sm"
          className="w-full justify-start"
          onClick={() => void logout()}
        >
          <LogOut className="mr-2 size-4" />
          Cerrar sesión
        </Button>
      </div>
    </aside>
  );
}
