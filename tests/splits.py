valut0 = "1,1,1|2,2,2"
valut0 = sum([int(i.split(",")[1]) for i in valut0.split("|")])
print(valut0)
