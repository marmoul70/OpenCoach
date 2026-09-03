import { registerModule } from '../../core/modules/registry'
import {
  registerWidget,
} from '../../core/widgets'
import {
  registerWidgetComponent,
} from '../../components/widgets/WidgetComponentRegistry'
import { CloudSun } from 'lucide-react'

import { WeatherWidget } from './WeatherWidget'

registerModule({
  id: 'weather',
  name: 'Météo',
  description: 'Conditions météorologiques et prévisions',
  enabled: true,
})

registerWidget({
  id: 'weather',
  moduleId: 'weather',
  title: 'Météo',
  description: 'Conditions météorologiques actuelles',
  status: 'success',
  accent: 'info',
  icon: CloudSun,
  enabled: true,
})

registerWidgetComponent(
  'weather',
  WeatherWidget,
)
