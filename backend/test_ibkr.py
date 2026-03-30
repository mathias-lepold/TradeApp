from ib_insync import IB, Stock

ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)

contract = Stock('MSFT', 'SMART', 'USD')
ib.qualifyContracts(contract)

bars = ib.reqHistoricalData(
    contract,
    endDateTime='',
    durationStr='1 D',
    barSizeSetting='5 mins',
    whatToShow='TRADES',
    useRTH=True
)

if bars:
    print(f"MSFT letzter Kurs: {bars[-1].close}")
    print(f"MSFT Volumen:      {bars[-1].volume}")
    print(f"MSFT Zeit:         {bars[-1].date}")
else:
    print("Keine Daten erhalten")

ib.disconnect()
print("Fertig!")



