# Istruzioni per eseguire la botnet

Su entrambi i sistemi è necessaria l'installazione di python e di pip.
Una volta installati eseguire (su entrambi i sistemi) il comando:

```
> pip install -r req.txt
```

per installare le librerie necessarie.

Il file CnC.py va eseguito con i permessi di root su una macchina con indirizzo IP 10.0.2.15 con il comando:
```
> sudo python3 CnC.py
```

Il file bot.py non necessita né dei permessi di root né di un IP statico. Per eseguirlo digitare il comando
```
> python3 bot.py
```
