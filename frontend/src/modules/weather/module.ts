import { registerModule } from '../../core/modules/registry'
import {
  registerWidget,
  registerWidgetView,
} from '../../core/widgets'
import {
  registerWidgetComponent,
} from '../../components/widgets/WidgetComponentRegistry'
import {
  registerWidgetViewComponent,
} from '../../components/widgets/WidgetViewRegistry'

import { CloudSun } from 'lucide-react'

import { WeatherWidget } from './WeatherWidget'
import { WeatherDetails } from './WeatherDetails'

registerModule({
  id: 'weather',
  name: 'Météo',
  description: 'Conditions météorologiques et prévisions',
  enabled: true,
})

registerWidgetView({
  id: 'weather-details',
  moduleId: 'weather',
  title: 'Météo',
})

registerWidgetViewComponent(
  'weather-details',
  WeatherDetails,
)

registerWidget({
  id: 'weather',
  moduleId: 'weather',
  title: 'Météo',
  description: 'Conditions météorologiques actuelles',
  status: 'success',
  accent: 'info',
  icon: CloudSun,
  enabled: true,
  detailsViewId: 'weather-details',
})

registerWidgetComponent(
  'weather',
  WeatherWidget,
)
