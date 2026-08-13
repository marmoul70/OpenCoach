import type { OpenCoachModule } from './types'

const modules: OpenCoachModule[] = []

export function registerModule(module: OpenCoachModule): void {
  modules.push(module)
}

export function getModules(): OpenCoachModule[] {
  return [...modules]
}

export function getModule(id: string): OpenCoachModule | undefined {
  return modules.find((module) => module.id === id)
}