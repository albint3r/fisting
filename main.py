from finsting.finsting import Finsting

price = 5000000
plazo = 5
enganche = price * 0.10
renta = (price * 0.05) / 12
plusvalia = 0.05

cf = Finsting(price, plazo, renta, enganche, plusvalia)
print(cf)
print(cf.renta_proyectada())