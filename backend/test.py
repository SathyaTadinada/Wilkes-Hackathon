from Models import Model, Wind

m = Model(84122, 0, 0, 0, 0, 0, 0)
print(m.getStation())
print(m.getAverageWeatherData())
print(m.getWeatherData("AWND"))

m = Model(84043, 0, 0, 0, 0, 0, 0)
print(m.getStation())
print(m.getAverageWeatherData())
print(m.getWeatherData("AWND"))

m = Model(84602, 0, 0, 0, 0, 0, 0)
print(m.getStation())
print(m.getAverageWeatherData())
print(m.getWeatherData("AWND"))

m = Wind(84122, 0.08, 20000, 0, 0, 0, 10)
print(m.getStation())
print(m.getAverageWeatherData())
print(m.getWeatherData("AWND"))
print(m.Pi)
print(m.NPVsub())

m = Wind(84043, 0.08, 20000, 0, 0, 0, 10)
print(m.getStation())
print(m.getAverageWeatherData())
print(m.getWeatherData("AWND"))
print(m.Pi)
print(m.NPVsub())

m = Wind(84602, 0.08, 20000, 0, 0, 0, 10)
print(m.getStation())
print(m.getAverageWeatherData())
print(m.getWeatherData("AWND"))
print(m.Pi)
print(m.NPVsub())