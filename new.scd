// CONFIGURING AND STARTING THE AUDIO SERVER with specific settings for
// - input devices
// - memory allocation

ServerOptions.inDevices;		 //to check the available input devices
Server.default.options.inDevice_("MacBook Pro Microphone");

// extensive audio processing requires adjusting the memory size
Server.default.options.memSize=8192*50;			//sets the memory size for the server. it allocates 409600 memory units for the server

s.boot; 										// boots the server


(
SynthDef(\reverb, {			// REVERB synth definition

	// arguments for the synth definition
	arg in = 98,	// input bus index
		processMode = 0, // 0 uses Control values for parameters, 1 uses Bus for any param suffix Bus
		gain = 0, mix = 1,
		processGain = 0, processGainBus = 99,
		preDelay = 0.001, bandwidth = 0.998,
		decayRate = 0.97, decayRateBus = 99,
		tailDensity = 0.7, damping = 0.0005,
		excursionDepth = 0.2, excursionRate = 5,
		shimmerPitch = 4, shimmerPitchBus = 99,
		out = 94;	// output bus index

	// LOCAL VARIABLES AND FUNCTIONS
	var sampleRate		= Server.default.sampleRate; 	//sample rate of the server

	var equalPower        = {							// to compute equal power panning values based on the 'mix' parameter
		arg mix = 0.5;
		[(1-mix).sqrt, mix.sqrt];
	};

	var sampSec           = {							// conversion samples to seconds
		arg numSamp, sampRate;
		numSamp / sampRate;
	};

	var gFacT60           = {							// computes gain factor for a given delay and decay rate
		arg delay, gFac;
		gFac.sign * (-3 * delay / log10(gFac.abs));

	};

	// some constant values

	var dSR = 29761;			// dSR = datorroSampleRate, sampleRate used in the paper.
	var maxExcursion = 32;		// samples

	// values for prep part: array containing pre-tank values for gain factors and times
	var preTankVals = [
		[0.75, 0.75, 0.625, 0.625], 				// gain-factors (gFacs) for pre-tank
		sampSec.value([142, 107, 379, 277], dSR) 	// time values for pre-tank
	].flop;

	// TANK PART VALUES

	// note that Dattorro flipped the sign of gFacs for the decaying all-pass filters,
	// I do that here so I don't worry about the signs later.

	var tankAP1GFac = -1 * tailDensity;		// gain factor for tank all-pass filter 1
	var tankAP1Time = 672;					// time value for tank all-pass filter 1
	var tankDel1    = sampSec.value(4453, dSR);		// delay time for tank delay 1

	var tankAP2GFac = (decayRate + 0.15).min(0.5).max(0.25);
	var tankAP2Time = sampSec.value(1800, dSR);
	var tankDel2    = sampSec.value(3720, dSR);

	var tankAP3GFac = tankAP1GFac;
	var tankAP3Time = 908;
	var tankDel3    = sampSec.value(4217, dSR);

	var tankAP4GFac = tankAP2GFac;
	var tankAP4Time = sampSec.value(2656, dSR);
	var tankDel4    = sampSec.value(3163, dSR);

	// SIGNAL INITIALIZATION: place-holder variables to process signals later
	var dry     = In.ar(in, 2);		// input signal
	var preTank = Silent.ar;
	var tank    = Silent.ar;
	var wetL    = Silent.ar;
	var wetR    = Silent.ar;
	var wet     = Silent.ar;
	var outs    = Silent.ar;

	// PARAMETER SELECTION AND MAPPING

	// pGain selects the processing gain value based on 'processMode'.
	// if 'processMode' is 0, it takes the 'processGain' value directly; otherwise, it reads from the 'processGainBus'
	var pGain = Select.kr(processMode, [processGain.dbamp, Lag.kr(In.kr(processGainBus), 0.05)]);		// PROCESSING GAIN

	// sPitch selects the shimmer pitch value based on 'processMode' as well
	var sPitch = Select.kr(processMode, [shimmerPitch, Lag.kr(In.kr(shimmerPitchBus), 0.05)]);			// SHIMMER PITCH

	var fback;		// feedback variable

	var dryAmp, wetAmp;
	#dryAmp, wetAmp = equalPower.value(mix);		// computes amplitude values for dry and wet signals

	// proper mappings for 'damping' and 'bandwidth' parameters
	damping = (damping + (1 + (8 * damping))).log / (10.log); 	// somewhat better than linear
	bandwidth = 3.pow(bandwidth) - (1 + bandwidth);


	// ROUTINGS

	// signal conversion from stereo to mono averaging the left and right channels
	preTank = (dry[0] + dry[1]) / 2;

	// applies pre-gain to the mono signal (based on 'processMode' parameter)
	preTank = preTank * pGain;

	// adds a short delay to the 'preTank' signal
	preTank = DelayC.ar(preTank, preDelay, preDelay);		//'DelayC.ar' is a delay line with max delay time 'preDelay' and delay time of 'preDelay'

	// lowpass filtering of the signal (reduce higher frequencies of the signal)
	preTank = LPF.ar(preTank, sampleRate / 2 * bandwidth);		// cut-off frequency is half the sampleRate * bandwidth

	// signal processing through series of 4 all-pass filters to diffuse input signal
	preTankVals.do({ arg pair; // 0: gain factor, 1: time
		preTank = AllpassC.ar(preTank, pair[1], pair[1], gFacT60.value(pair[1], pair[0]));		//gFacT60 computes delay time and feedback coefficient used to configure allpass
	});

	fback = LocalIn.ar(1);		// local audio bus initialization for feedback processing. this will be used to route the feedback signal within the reverb effect

	// // TANK STARTS HERE: main reverb tank processing

	// first branch: all pass filter with modulated delay time and decay time to the input ('preTank'+feedback signal)
	tank  = AllpassC.ar(preTank + (decayRate * fback),
		maxdelaytime: sampSec.value(tankAP1Time + maxExcursion, dSR),
		delaytime: sampSec.value(tankAP1Time, dSR)
		+ (sampSec.value(maxExcursion, dSR) * excursionDepth * SinOsc.ar(excursionRate)),		// the sine wave oscillator creates a slight fluctuation in delay time, contributing to the reverb's character
		decaytime: gFacT60.value(sampSec.value(tankAP1Time, dSR), tankAP1GFac)
	);

	// adding wet signals: processed signal is split and added to the left and right channels with some delay and gain adjustments
	     wetL = -0.6 * DelayC.ar(tank, sampSec.value(1990, dSR), sampSec.value(1990, dSR)) + wetL;
	     wetR = 0.6 * tank + wetR;
	     wetR = 0.6 * DelayC.ar(tank, sampSec.value(3300, dSR), sampSec.value(3300, dSR)) + wetR;

	// more delay lines and filtering to further diffuse the signal and modify the reverb tail + adjustments to wet signals (L and R)
	tank = DelayC.ar(tank, tankDel1, tankDel1);
	tank = LPF.ar(tank, sampleRate / 2 * (1 - damping)) * decayRate;
	     wetL = -0.6 * tank + wetL;
	tank = AllpassC.ar(tank, tankAP2Time, tankAP2Time, gFacT60.value(tankAP2Time, tankAP2GFac));
	     wetR = -0.6 * tank + wetR;
	tank = DelayC.ar(tank, tankDel2, tankDel2);
	     wetR = 0.6 * tank + wetR;

	//  second branch: processing happens similarly to what's been done in the first branch,
	// slight variations contribute to creating a different texture in the reverb tail
	tank  = AllpassC.ar((tank * decayRate) + preTank,
		maxdelaytime: sampSec.value(tankAP3Time + maxExcursion, dSR),
		delaytime: sampSec.value(tankAP3Time, dSR)
		+ (sampSec.value(maxExcursion, dSR) * excursionDepth * 0.8 * SinOsc.ar(excursionRate * 0.8)),
		decaytime: gFacT60.value(sampSec.value(tankAP3Time, dSR), tankAP3GFac)
	);

		// more wet signals are added
	     wetL = 0.6 * tank + wetL;
	     wetL = 0.6 * DelayC.ar(tank, sampSec.value(2700, dSR), sampSec.value(2700, dSR)) + wetL;
	     wetR = -0.6 * DelayC.ar(tank, sampSec.value(2100, dSR), sampSec.value(2100, dSR)) + wetR;

	// to further enhance the reverb effect (similar operations to the ones performed in the first branch)
	tank = DelayC.ar(tank, tankDel3, tankDel3);
	tank = LPF.ar(tank, sampleRate / 2 * (1 - damping)) * decayRate;
	tank = AllpassC.ar(tank, tankAP4Time, tankAP4Time, gFacT60.value(tankAP4Time, tankAP4GFac));

		 wetL = -0.6 * tank + wetL;
	     wetR = -0.6 * DelayC.ar(tank, sampSec.value(200, dSR), sampSec.value(200, dSR)) + wetR;

	tank = DelayC.ar(tank, tankDel4, tankDel4);
	     wetL = 0.6 * tank + wetL;

	// final decay addition to the signal
	tank = tank * decayRate;

	// // Sloppy Shimmering
	tank = PitchShift.ar(tank, pitchRatio: sPitch, mul: Select.kr(sPitch > 1, [1, 2.dbamp]));

	// // TANK ENDS HERE
	LocalOut.ar(tank);		// outputs the final reverb-processed signal to a local audio bus

    wet = [wetL, wetR];		// R and L signals combined back into a stereo signalarray

	wet = HPF.ar(wet, 40); 	// high-pass filtering to prevent lows from blowing up

	outs = (dry * dryAmp) + (wet * wetAmp);		// dry and wet signals scaling and combination into 'outs' signal

	// the scaling factors determined by the 'equalPower' function ensures a smooth blend between dry and wet signal

	outs = outs * gain.dbamp;		// 'outs' is scaled by the overall gain
									// to convert the gain from dB to a linear amplitude factor

	Out.ar(out, outs);		// output bus
}).add;




// PAULSTRETCH-MONO synth: implements a paulstretch-like effect for time stretching the audio using granular synthesis and FFT processing
// the audio buffer is stretched in time, diffused in the frequency domain and modulated by an envelope

SynthDef(\paulstretchMono, {

	//arguments initialization to perform granular synthesis
	|out = 0, bufnum, envBufnum, pan = 0, stretch = 50000, window = 0.5, rate1=0.5, rate2=1.7, rate3=1, rate4=1.5, ampf1=0.1, ampf2=0.09, ampf3=0.8, ampf4=0.7, amp=0.8, gate=0.0, dur=1|

	var trigPeriod, sig, chain, trig, pos, fftSize, env;

	env = Env([0, amp, 0], [dur/2, dur/2]);		// amplitude envelope going up to 'amp' and back to 0 over 'dur' time

	fftSize = 2**floor(log2(window*SampleRate.ir));

	trigPeriod = fftSize/SampleRate.ir;			// period trigger based on fftSize
	trig = Impulse.ar(1/trigPeriod);			// impulse generation at period 'trigPeriod'

	pos = Demand.ar(trig, 0, demandUGens: Dseries(0, trigPeriod/stretch)); //positions for the grains generated at demand rate UGen

	// actual grain synthesis: 2 grains are generated using different starting positions to create stereo width
	sig = [(GrainBuf.ar(1, trig, trigPeriod, bufnum, rate1, pos, envbufnum: envBufnum)),
			(GrainBuf.ar(1, trig, trigPeriod, bufnum, rate1, pos + (trigPeriod/(2*stretch)), envbufnum: envBufnum))]*amp;		// grains are scaled by 'amp'

	sig = sig.collect({ |item, i|
		chain = FFT(LocalBuf(fftSize), item, hop: 1.0, wintype: -1);

		chain = PV_Diffuser(chain, 1 - trig);		// phase vocoder diffusion effect

		item = IFFT(chain, wintype: -1);
	});

	sig = sig*PlayBuf.ar(1, envBufnum, 1/(trigPeriod), loop:1);		// signal modulated by an envelope

	sig[1] = DelayC.ar(sig[1], trigPeriod/2, trigPeriod/2);			// delay applied to the 2nd channel to enhance stereo effect

	// signal mixed, panned and sent to output
	Out.ar(98, Pan2.ar(Mix.new(sig)*EnvGen.kr(env, doneAction: Done.freeSelf), pan));	// envgen used to generate the envelope, 'Done.freeSelf' to free the synth when done
}).add;


// implements a synth to obtain a clearer sound through reverb, high and low pass filtering
SynthDef(\clean, {
	arg amp=1, freq=100;
	var in;
	in=In.ar(98, 2);		// reads a stereo input from bus 98 (PAULSTRETCH synth)
	in=FreeVerb2.ar(in[0], in[1], 1, 1, 0.8);		// stereo reverb effect
	in=HPF.ar(in, freq: 300.0);
	in=LPF.ar(in, freq: freq);
	Out.ar(0, in*amp);
}).add;

// implements a synth to obtain a complex shimmering wet effect through layers of distortion, reverb and filtering effects

SynthDef(\shimmerwet, {
	arg amp=1, cutoff=1200;
	var in;
	in=In.ar(94, 2);		// reads a stereo input from bus 94 (REVERB synth)
	3.do{in=in.distort;									// distortion effect
	in=FreeVerb2.ar(in[0], in[1], 0.93, 1, 0.8);		// stereo reverb effect
	in=HPF.ar(in, freq: 1500.0);						// high-pass filtering
	in=LPF.ar(in, freq: cutoff);};						// low-pass filtering
	Out.ar(0, in*amp);							// output on bus 0, signal scaled by 'amp'
}).add;


// SYNTH INSTANCES CREATION
a=Synth.new(\clean);
y=Synth.new(\shimmerwet);
z=Synth.new(\reverb);


// BUFFERS AND ENVELOPES SETUP
{
	var envBuf, envSignal, buffer;
	~buffer = Buffer.readChannel(s, thisProcess.nowExecutingPath.dirname +/+ "string1.wav"); //reads the audio file into a buffer
	// The grain envelope
	~envBuf = Buffer.alloc(s, s.sampleRate, 1);			// buffer allocation for the envelope with the same length as the sample rate (1 second duration)
	envSignal = Signal.newClear(s.sampleRate).waveFill({|x| (1 - x.pow(2)).pow(1)}, -1.0, 1.0);		// new signal filled with a parabolic envelope shape
	~envBuf.loadCollection(envSignal);		// loads the signal into the envelope buffer
	s.sync();								// synchronizes the server
}.fork;		// runs this block into a separate thread without interfering with the rest of the processing


//OSC HANDLER SETUP
OSCdef.new(\0,		// '\0' is the name of the OSC handler
	{
		arg msg;	// 'msg' as input
		postln(msg);

		// new instance of the 'paulstretchMono' synth
		// paramenters passed include buffer numbers for the audio and envelope buffers, rate and amplitude settings (received from OSC message)
		// '\rate1' is calculated with 'msg[1]', which is converted from MIDI note number to frequency ratio
		// '\amp' is scaled using 'msg[2].linexp(...)', mapping a MIDI velocity range to an amplitude range
		x=Synth.new(\paulstretchMono, [\bufnum, ~buffer.bufnum, \envBufnum, ~envBuf.bufnum, \rate1, 2**((msg[1]-24)/12), \dur, 2*msg[4], \amp, msg[2].linexp(0, 127, 0.5, 1)]);

		//x.set(\rate1, 2**((msg[1])/12));
		//x.set(\gate, 1.0);
		//{x.set(\gate, 0.0)}.defer(0.1);
		//{BPF.ar(WhiteNoise.ar, [msg[1]-12, msg[1]-12 ].midicps, 1e-5, Env.sine(4*msg[4]).kr(msg[2])).sum!2 * 200}.play;
	},
	'/numbers',		// the OSCdef listens for messages on the '/numbers' address
	nil,			// from any sender
	57120			// on the specified port
);


	b = NetAddr.new("127.0.0.1", 57000);		// new network address object creation
	// Funzione che manda numeri causali che rappresentano il set_order del markov model
	~valori = [3, 4, 5, 6, 7, 8];		// array of values representing possible 'set_order' values for the Markov Model

	~close = Routine.new({
		inf.do {		// infinite loop
			var chosen = ~valori.choose;			// randomly selects a number from 'valori' array
			chosen.postln;
			b.sendMsg("/closeness", chosen);		// sends and OSC message with the address '/closeness'
			3.wait;									// 3sec wait before repeating the loop
	        }
    }).play;

)

//SYNTH PARAMETERS

a.set(\amp, 0);
a.set(\freq, 500);
y.set(\amp, 1);
y.set(\cutoff, 1000);

s.quit;		// to stop the server and running synths, frees allocated resources


//z.set(\shimmerPitch, 2);
//z.set(\shimmerPitch, 1);
//z.set(\gain, 0);
//z.set(\decayRate, 0.97);
//z.set(\damping, 0.00000005);
//z.set(\excursionRate, 5);
//z.set(\bandwidth, 0.998);
//z.set(\mix, 0.7);
//x.set(\stretch, 2);

/*
		processMode = 0, // 0 uses Control values, 1 uses Bus for any param suffix Bus.
		gain = 0, mix = 0.35,
		processGain = 0, processGainBus = 99,
		preDelay = 0.001, bandwidth = 0.998,
		decayRate = 0.9, decayRateBus = 99,
		tailDensity = 0.7, damping = 0.0005,
		excursionDepth = 0.2, excursionRate = 2,
		shimmerPitch = 2, shimmerPitchBus = 99,
		out = 0;
*/

/*
x.set(\rate1, 0.5); //0.5 0.56 0.65 0.67 0.75 0.85 0.9
x.set(\rate1, 0.56);
x.set(\rate1, 0.65);
x.set(\rate1, 0.67);
x.set(\rate1, 0.75);
x.set(\rate1, 0.85);
x.set(\rate1, 0.9);
x.set(\rate1, 4);
x.set(\amp, 0);
x.free
//subtractive synthesis
{BPF.ar(WhiteNoise.ar, [76, 80].midicps, 1e-5, Env.sine(10).kr(2)).sum!2 * 50}.play;


{EnvGen.kr(Env([0, 2, 0], [0.5, 0.5]), Impulse.kr(1))}.plot(5);
Env.new([0.01, 2, 0.01], [3, 7], [-3, 4]).plot
Env.new([0, 1, 0], [8, 12], [-1, 2]).plot
{Env.sine(2).kr(0.1)}.plot(5)

//thisProcess.platform.recordingsDir

(
~b3 = Buffer.readChannel(s, thisProcess.nowExecutingPath.dirname +/+ "Voice.mp3", channels: 0);

// audio
SynthDef.new("rat", {
	arg out = 0, tFreq =15, dur = 0.1, rate = 1, pos = 0.8;
	var sig, env, attack=0, decay=1, ratio;


	ratio=Impulse.ar(tFreq);




	//env =  EnvGen.ar(Env([0, 1, 0], [attack, decay], curve: 0), Impulse.kr(1/(attack+decay)));

	sig=GrainBuf.ar(
		numChannels: 2,
		trigger: ratio,
		dur: dur,
		sndbuf: ~b3,
		rate: rate,
		//pos: (pos+LFSaw.ar(10*1/BufDur.ir(~b3)).range(0, (BufSamples.ir(~b3)-1)/10)),
		pos: 0.8-LFSaw.ar(1/(10*BufDur.ir(~b3))),
		//pos: pos,
		interp: 2,
		pan: 0,
		envbufnum: -1,
		maxGrains: 512);

	//sig = sig*env;
	Out.ar(99, FreeVerb.ar(sig, 0, 1, 0.1, 10, 0));

}).add;

y = Synth.new(\rat);
)

y.free

*/