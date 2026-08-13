export interface WidgetView {
  id: string
  moduleId: string
  title: string
}

const views: WidgetView[] = []

export function registerWidgetView(view: WidgetView): void {
  if (views.some((registeredView) => registeredView.id === view.id)) {
    throw new Error(`Vue de widget déjà enregistrée : ${view.id}`)
  }

  views.push(view)
}

export function getWidgetView(id: string): WidgetView | undefined {
  return views.find((view) => view.id === id)
}

export function getWidgetViewsByModule(moduleId: string): WidgetView[] {
  return views.filter((view) => view.moduleId === moduleId)
}
