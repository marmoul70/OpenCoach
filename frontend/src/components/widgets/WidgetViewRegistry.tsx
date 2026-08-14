import type { ComponentType } from 'react'

export type WidgetViewComponent = ComponentType<any>

const views = new Map<string, WidgetViewComponent>()

export function registerWidgetViewComponent(
  id: string,
  component: WidgetViewComponent,
): void {
  if (views.has(id)) {
    throw new Error(`Composant de vue déjà enregistré : ${id}`)
  }

  views.set(id, component)
}

export function getWidgetViewComponent(
  id: string,
): WidgetViewComponent | undefined {
  return views.get(id)
}
