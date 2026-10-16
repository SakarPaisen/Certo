def celsius_to_fahrenheit_table(start, stop, step):
    if step == 0:
        raise ValueError("step must not be zero")
    if (stop - start) * step < 0:
        raise ValueError("step moves away from stop")
    rows = []
    celsius = start
    while (step > 0 and celsius <= stop) or (step < 0 and celsius >= stop):
        rows.append((celsius, round(celsius * 9 / 5 + 32, 1)))
        celsius += step
    return rows
