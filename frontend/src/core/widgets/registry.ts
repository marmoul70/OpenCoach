import type { WidgetDefinition } from './types'

const widgets: WidgetDefinition[] = []

export function registerWidget(widget: WidgetDefinition): void {
  if (widgets.some((registeredWidget) => registeredWidget.id === widget.id)) {
    throw new Error(`Widget déjà enregistré : ${widget.id}`)
  }

  widgets.push(widget)
}

export function getWidgets(): WidgetDefinition[] {
  return [...widgets]
}

export function getWidget(id: string): WidgetDefinition | undefined {
  return widgets.find((widget) => widget.id === id)
}

export function getWidgetsByModule(moduleId: string): WidgetDefinition[] {
  return widgets.filter((widget) => widget.moduleId === moduleId)
}
