export interface WeatherLocation {
  latitude: number
  longitude: number
  name?: string
}


export interface CurrentWeather {
  temperature: number
  apparentTemperature: number
  humidity: number
  precipitation: number
  windSpeed: number
  windGusts: number
  weatherCode: number
  time: string
}


export interface HourlyWeather {
  time: string
  temperature: number
  apparentTemperature: number
  humidity: number
  precipitationProbability: number
  precipitation: number
  weatherCode: number
  windSpeed: number
  windGusts: number
}


export interface DailyWeather {
  date: string
  weatherCode: number
  temperatureMax: number
  temperatureMin: number
  precipitationProbabilityMax: number
  precipitationSum: number
  windSpeedMax: number
  windGustsMax: number
  uvIndexMax: number
  sunrise: string
  sunset: string
}


export interface WeatherData {
  location: WeatherLocation
  current: CurrentWeather
  hourly: HourlyWeather[]
  daily: DailyWeather[]
}
