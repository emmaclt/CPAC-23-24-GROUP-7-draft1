s.boot
NetAddr.langPort;
(
b = NetAddr.new("127.0.0.1", 57000);
// Funzione che manda numeri causali che rappresentano il set_order del markov model
~valori = [1, 2, 3, 4, 5, 6, 7, 8];
~close = Routine.new({
    inf.do {
        var chosen = ~valori.choose;
		chosen.postln;
		b.sendMsg("/closeness", chosen);
        1.wait;
    }
}).play;
)


(
x = OSCFunc( { |msg, time, addr, recvPort|
    // Estrai i numeri dal messaggio
    var num1 = msg[1].asInteger;
    var num2 = msg[2].asInteger;
    var num3 = msg[3].asInteger;

    // Stampa i numeri nella console
    [num1, num2, num3].postln;
}, '/numbers');
)
s.quit;