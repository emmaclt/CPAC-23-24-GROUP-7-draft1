s.boot

(
SynthDef(\clean, {
	arg amp, freq, time;
	var env = Env([0, amp, 0], [time/1000, time/200]);
	var in;
	in=SinOsc.ar(freq)*EnvGen.kr(env, doneAction: Done.freeSelf);
	Out.ar([0,1], in*0.1);
}).add;




OSCdef.new(\0,
	{
		arg msg;
		x=Synth.new(\clean, [\freq, msg[2].midicps, \amp, msg[3].linexp(0, 127, 0.5, 1), \time, 3*msg[4]]);
		postln('');
		postln(msg[1]);
		postln(msg[2]);
		postln(msg[3]);
		postln(msg[4]);
	},
	'/0',
	nil,
	7001
);
)

